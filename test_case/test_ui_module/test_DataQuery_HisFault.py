import pytest
import os
import sys
from playwright.sync_api import sync_playwright, expect

# --- 引入现有框架组件 ---
# 假设项目根目录已加入 sys.path，或者通过相对导入
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.data_reader import DataReader  # 对应你的 data_reader.py
from common.mysql_connect import DatabasePool  # 对应你的 mysql_connect.py
from common.login_handler import LoginHandler  # 新建的登录模块

# 初始化单例
db_pool = DatabasePool()
login_handler = LoginHandler()


# --- 辅助函数：动态构建 SQL ---
def build_fault_sql(filters):
    """根据 Excel 中的过滤条件动态构建 SQL"""
    sql = "SELECT fault_time, fault_type, station_name, device_name, fault_status FROM t_history_fault WHERE 1=1"
    params = []

    # 搜索词 (模糊匹配厂站或设备)
    if filters.get('search_word') and filters['search_word'] != '-':
        sql += " AND (station_name LIKE %s OR device_name LIKE %s)"
        word = f"%{filters['search_word']}%"
        params.extend([word, word])

    # 10kV 筛选 (假设字段名为 voltage_level)
    if filters.get('is_10kv') == '是':
        sql += " AND voltage_level = '10kV'"

    # 故障类型
    if filters.get('fault_type') and filters['fault_type'] != '-':
        sql += " AND fault_type = %s"
        params.append(filters['fault_type'])

    # 故障状态
    if filters.get('fault_status') and filters['fault_status'] != '-':
        sql += " AND fault_status = %s"
        params.append(filters['fault_status'])

    # 时间范围
    if filters.get('start_time') and filters['start_time'] != '-':
        sql += " AND fault_time >= %s"
        params.append(filters['start_time'])

    if filters.get('end_time') and filters['end_time'] != '-':
        # 包含结束日期当天 23:59:59
        sql += " AND fault_time <= %s"
        params.append(f"{filters['end_time']} 23:59:59")

    # 排序必须与前端一致，否则内容比对会失败
    sql += " ORDER BY fault_time DESC"

    return sql, params


# --- 辅助函数：数据标准化 (用于比对) ---
def normalize_data(row, source):
    """将 DB/API/UI 的数据统一格式，只保留关键字段"""
    try:
        if source == 'db':
            # row 是字典 {'fault_time': datetime..., 'fault_type': '...'}
            t = row['fault_time']
            time_str = t.strftime("%Y-%m-%d %H:%M:%S") if hasattr(t, 'strftime') else str(t)
            return (time_str, row['fault_type'], row['station_name'], row['device_name'])

        elif source == 'api':
            # row 是 API 返回的字典，字段名可能是驼峰
            return (row['faultTime'], row['faultType'], row['stationName'], row['deviceName'])

        elif source == 'ui':
            # row 是从页面提取的字典
            return (row['time'], row['type'], row['station'], row['device'])
    except Exception as e:
        print(f"⚠️ 数据格式化错误：{e}, 原始数据：{row}")
        return None


class TestDataQueryConsistency:

    @pytest.mark.parametrize("row", DataReader.read_excel("fault_query_data.xlsx", sheet_name="Sheet1"))
    def test_fault_query_three_way_check(self, row):
        """
        数据一致性校验：DB vs API vs UI
        row 是 Excel 中的一行数据 (列表)，索引对应列
        假设 Excel 列顺序：0:用例编号，1:搜索词，2:是否 10kV，3:故障类型，4:故障状态，5:开始时间，6:结束时间，7:校验策略
        """

        # 1. 解析 Excel 行数据为字典，方便处理
        # 注意：如果你的 read_excel 返回的是二维列表，需要手动映射索引
        # 建议修改 data_reader 返回 List[Dict] 或者在这里映射
        filters = {
            'case_id': row[0],
            'search_word': row[1] if row[1] != '-' else None,
            'is_10kv': row[2],
            'fault_type': row[3] if row[3] != '-' else None,
            'fault_status': row[4] if row[4] != '-' else None,
            'start_time': row[5] if row[5] != '-' else None,
            'end_time': row[6] if row[6] != '-' else None,
            'strategy': row[7]
        }

        print(f"\n🚀 执行用例：{filters['case_id']} - {row[8] if len(row) > 8 else ''}")

        # ================= 2. 获取 DB 数据 (基准) =================
        sql, params = build_fault_sql(filters)
        conn = db_pool.get_connection()  # 复用你的连接池
        cursor = conn.cursor()
        try:
            cursor.execute(sql, params)
            db_data = cursor.fetchall()  # 获取所有结果
        finally:
            cursor.close()
            conn.close()  # 记得归还连接或关闭，视你的连接池实现而定

        # ================= 3. 获取 API 数据 =================
        # 这里需要调用你的 http_client 或者直接 requests
        # 假设你有一个通用的 post 方法
        api_payload = {
            "searchWord": filters['search_word'],
            "is10kV": filters['is_10kv'] == '是',
            "faultType": filters['fault_type'],
            "faultStatus": filters['fault_status'],
            "startTime": filters['start_time'],
            "endTime": filters['end_time'],
            "pageNum": 1,
            "pageSize": 100
        }
        # 清理 None 值
        api_payload = {k: v for k, v in api_payload.items() if v is not None}

        # ⚠️ 替换为你真实的 API 地址和 Header (需要 Token)
        # 先确保登录获取了 Token
        token = login_handler.get_token_via_api()
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

        import requests
        resp = requests.post("https://your-app.com/api/v1/faults/query", json=api_payload, headers=headers)
        resp.raise_for_status()
        api_resp = resp.json()
        api_data = api_resp['data']['list']  # 根据实际返回结构调整

        # ================= 4. UI 自动化操作 =================
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()

            # 👉 关键：注入登录态
            login_handler.inject_auth_to_context(context)

            page = context.new_page()
            page.goto("http://192.168.2.226:35200/dsp-api/api/qiz-pg-fault-analysis-nc/smEventResultFault/selectAll")
            page.wait_for_load_state("networkidle")

            # --- 执行 UI 查询操作 ---
            # 填充搜索词
            if filters['search_word']:
                page.fill("input[placeholder='请输入']", filters['search_word'])

            # 勾选 10kV
            if filters['is_10kv'] == "是":
                checkbox = page.locator("input[type='checkbox']")  # 需确认 selector
                if not checkbox.is_checked():
                    checkbox.check()

            # 选择时间 (简化处理，实际需点击日期控件)
            if filters['start_time']:
                page.fill("input[placeholder='开始日期']", filters['start_time'])
                page.fill("input[placeholder='结束日期']", filters['end_time'])

            # 点击查询
            page.click("button:has-text('查询')")
            page.wait_for_load_state("networkidle")
            page.wait_for_selector(".ant-table-tbody tr", timeout=10000)

            # --- 提取 UI 数据 ---
            rows = page.query_selector_all(".ant-table-tbody tr")
            ui_data = []
            for r in rows:
                cells = r.query_selector_all("td")
                if len(cells) >= 5:
                    # 根据截图列顺序提取：时间(2), 类型(5), 状态(7), 厂站(3), 设备(4)
                    # 索引从 0 开始，所以时间是 cells[1]
                    ui_item = {
                        'time': cells[1].inner_text().strip(),
                        'station': cells[2].inner_text().strip(),
                        'device': cells[3].inner_text().strip(),
                        'type': cells[4].inner_text().strip(),
                        'status': cells[6].inner_text().strip()
                    }
                    ui_data.append(ui_item)

            browser.close()

        # ================= 5. 三方一致性断言 =================
        print(f"📊 数据量 -> DB:{len(db_data)} | API:{len(api_data)} | UI:{len(ui_data)}")

        # 策略检查
        if filters['strategy'] == 'Zero_Check':
            assert len(db_data) == 0 and len(api_data) == 0 and len(ui_data) == 0, "❌ 预期为空，但查到了数据"
            print("✅ Zero_Check 通过")
            return

        # 数量检查
        assert len(db_data) == len(api_data), f"❌ DB({len(db_data)}) 与 API({len(api_data)}) 数量不一致"
        assert len(api_data) == len(ui_data), f"❌ API({len(api_data)}) 与 UI({len(ui_data)}) 数量不一致"

        # 内容检查 (Set 比对)
        db_set = set(normalize_data(r, 'db') for r in db_data if normalize_data(r, 'db'))
        api_set = set(normalize_data(r, 'api') for r in api_data if normalize_data(r, 'api'))
        ui_set = set(normalize_data(r, 'ui') for r in ui_data if normalize_data(r, 'ui'))

        assert db_set == api_set, "❌ DB 与 API 内容不一致"
        assert api_set == ui_set, "❌ API 与 UI 内容不一致"

        print("✅ 三方数据完全一致！")