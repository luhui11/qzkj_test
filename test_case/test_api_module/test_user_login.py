import pytest
import sys
import os
import json
import allure

# --- 项目路径配置 ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from common.data_reader import DataReader
from common.http_client import HttpClient
from common.assert_tool import AssertTool
from common.log_handler import logger

# --- 全局常量 ---
EXCEL_PATH = r"E:\pythonProject/qzkj_test/test_data/user_login.xlsx"
SHEET_NAME = "login"

# --- 预加载测试数据 ---
try:
    raw_data = DataReader.read_excel(EXCEL_PATH, SHEET_NAME)
    if not raw_data or len(raw_data) < 2:
        logger.warning(f"未读取到有效测试数据，文件：{EXCEL_PATH}")
        GLOBAL_LOGIN_DATA = [{}]
    else:
        headers = raw_data[0]
        GLOBAL_LOGIN_DATA = []
        for row in raw_data[1:]:
            row_dict = {}
            for i, value in enumerate(row):
                if i < len(headers):
                    # 读取时立即去除首尾空白字符，防止 Excel 中的空格导致 400
                    val_str = str(value).strip() if value is not None else ""
                    row_dict[headers[i]] = val_str
            GLOBAL_LOGIN_DATA.append(row_dict)
    logger.info(f"成功加载 {len(GLOBAL_LOGIN_DATA)} 条登录测试数据")
except Exception as e:
    logger.error(f"加载测试数据失败：{e}")
    GLOBAL_LOGIN_DATA = [{}]


@allure.feature("登录模块")
@allure.story("登录功能")
class TestLoginWithAssertTool:
    """用户登录测试用例类 """

    @pytest.fixture(scope="function")
    def client(self):
        """初始化 HttpClient"""
        client = HttpClient()

        # 设置通用请求头
        client.session.headers.update({
            'Accept': 'application/json, text/plain, */*',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            # 不强制设置 Content-Type，让 requests 库根据 data= 自动处理
            # 这样能确保编码最标准
        })

        client.set_auth_token("")
        yield client
        client.session.close()

    @pytest.mark.parametrize(
        "case_data",
        GLOBAL_LOGIN_DATA,
        ids=lambda x: f"{x.get('case_id', 'UNKNOWN')}" if isinstance(x, dict) else "unknown"
    )
    def test_login_workflow(self, client, case_data):
        """
        登录业务流测试
        """
        # --- 0. 数据校验 ---
        if not case_data or not isinstance(case_data, dict) or not case_data.get("account"):
            logger.warning("跳过无效测试数据")
            pytest.skip("测试数据无效或缺少 account 字段")

        # --- 1. 提取并清洗测试数据 ---
        case_id = case_data.get("case_id", "unknown")
        title = case_data.get("title", "无标题")

        # 再次清洗：确保没有残留空格
        account = case_data.get("account", "").strip()
        password = case_data.get("password", "").strip()
        client_id = case_data.get("client_id", "").strip()

        # 获取预期结果
        try:
            expected_code = int(case_data.get("expected_code", 200))
        except ValueError:
            expected_code = 200

        expected_msg = case_data.get("expected_msg", "")
        check_token = str(case_data.get("expected_token", "")).lower().strip()

        logger.info(f"\n{'=' * 30} [开始执行] {case_id}: {title} {'=' * 30}")
        logger.info(f"账号：{account}")
        logger.info(f"密码：{password[:8]}")
        logger.info(f"ClientID: {client_id}")
        logger.info(f"预期返回码：{expected_code}")

        # --- 2. 构造请求体 (Form Data) ---
        payload = {
            "account": account,
            "password": password,
            "client_id": client_id
        }

        logger.debug(f"请求 Payload: {payload}")

        # --- 3. 发送请求 ---
        try:
            # 使用 data= 发送 application/x-www-form-urlencoded
            response = client.post("/Login", data=payload)
        except Exception as e:
            logger.error(f"请求发送异常：{e}")
            pytest.fail(f"网络请求失败：{str(e)}")

        # --- 4. 断言结果 ---
        # 4.1 解析 JSON 响应 (无论 HTTP 状态码是多少，先尝试解析)
        try:
            res_json = response.json()
        except ValueError:
            # 如果返回的不是 JSON (比如 Nginx 报错页)，则直接根据 HTTP 状态码判断
            logger.warning(f"响应非 JSON 格式：{response.text[:200]}")
            res_json = {}
            actual_business_code = response.status_code
        else:
            # 优先取响应体中的 code 字段作为“业务状态码”
            actual_business_code = res_json.get("code")

            # 如果响应体里没有 code 字段，降级使用 HTTP 状态码
            if actual_business_code is None:
                actual_business_code = response.status_code

        logger.info(f"HTTP 状态码：{response.status_code}")
        logger.info(f"业务状态码 (code)：{actual_business_code}")
        logger.info(f"响应消息：{res_json.get('msg', '')}")

        # 4.2 业务状态码必须与 Excel 一致
        assert actual_business_code == expected_code, \
            f"业务状态码断言失败！\n用例：{case_id}\n期望 code: {expected_code}\n实际 code: {actual_business_code}\n响应内容：{json.dumps(res_json, ensure_ascii=False)}"

        logger.info(f"业务状态码验证通过：{actual_business_code}")

        # 4.3 断言响应消息 (如果有预期消息)
        if expected_msg:
            actual_msg = res_json.get("msg") or res_json.get("message") or ""
            assert expected_msg in actual_msg, \
                f"消息断言失败！\n期望包含：'{expected_msg}'\n实际消息：'{actual_msg}'"
            logger.info(f"消息断言通过：{actual_msg}")

        # 4.4 业务场景断言：检查 Token (仅当成功且需要校验时)
        # 只有当 业务码==200 且 Excel 标记需要检查 token 时才执行
        if actual_business_code == 200 and check_token == "yes":
            try:
                # 确保 data 字段存在
                assert "data" in res_json, "响应中缺少 'data' 字段"
                data_obj = res_json["data"]

                # 确保 token 字段存在
                assert "token" in data_obj, "响应 data 中缺少 'token' 字段"

                token_val = data_obj["token"]
                assert token_val and len(token_val) > 5, f"Token 格式异常：{token_val}"

                logger.info(f"Token 获取成功：{token_val[:15]}...")
            except Exception as e:
                logger.error(f"Token 校验失败：{str(e)}")
                raise

        logger.info(f"✅[通过] 用例 {case_id}:{title} 执行完毕")
