import os
import subprocess
import sys
from datetime import datetime

# 项目根目录 (自动获取当前脚本所在目录)
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
TEST_DIR = os.path.join(PROJECT_ROOT, "test_case")
BASE_REPORT_DIR = os.path.join(PROJECT_ROOT, "report")

# 生成当前时间戳文件夹名称 (格式：YYYYMMDD_HHMM)
timestamp = datetime.now().strftime("%Y%m%d_%H%M")
RUN_REPORT_DIR = os.path.join(BASE_REPORT_DIR, timestamp)

# 定义子目录
RAW_DIR = os.path.join(RUN_REPORT_DIR, "allure_raw")
HTML_DIR = os.path.join(RUN_REPORT_DIR, "allure_html")

def main():
    print(f"开始执行测试...")
    print(f"当前时间标识: {timestamp}")
    print(f"本次报告保存路径: {RUN_REPORT_DIR}")

    # 1. 创建目录 (如果不存在)
    os.makedirs(RAW_DIR, exist_ok=True)
    os.makedirs(HTML_DIR, exist_ok=True)
    print(f"目录已准备就绪:\n   - Raw: {RAW_DIR}\n   - Html: {HTML_DIR}")

    # 2. 运行 Pytest 生成 Allure Raw 数据
    pytest_cmd = [
        sys.executable,
        "-m", "pytest",
        TEST_DIR,
        "--alluredir", RAW_DIR,
        "-v",
        "--tb=short",
        "--import-mode=prepend"  # 关键点：强制使用 prepend 模式
    ]

    print("\n 正在执行测试用例...")

    # 使用 env 参数确保 PYTHONPATH 生效
    # 使用 check=False 以确保即使测试失败也能生成报告
    result = subprocess.run(
        pytest_cmd,
        cwd=PROJECT_ROOT,  # 关键点：切换工作目录到项目根
        env={**os.environ, "PYTHONPATH": PROJECT_ROOT},  # 关键点：设置环境变量
        check=False
    )

    if result.returncode != 0:
        print(f"\n测试执行完毕，但有用例失败 (退出码: {result.returncode})。将继续生成报告...")
    else:
        print("\n所有测试用例通过！")

    # 3. 生成 Allure HTML 报告 (保持不变)
    ALLURE_BIN_PATH = r"D:\tools\allure-2.38.1\bin\allure.bat"
    allure_generate_cmd = [
        ALLURE_BIN_PATH, "generate",
        RAW_DIR,
        "-o", HTML_DIR,
        "--clean"
    ]

    print("\n▶️ 正在生成 HTML 报告...")
    try:
        subprocess.run(allure_generate_cmd, check=True)
        print(f"✅ HTML 报告生成成功！")
    except FileNotFoundError:
        print("\n❌ 错误：未找到 'allure' 命令。")
        print(" 请确保已安装 allure-commandline 并配置了环境变量。")
        return
    except subprocess.CalledProcessError as e:
        print(f"\n❌ 生成报告失败: {e}")
        return

    # 4. 输出最终指引 (保持不变)
    index_html_path = os.path.join(HTML_DIR, "index.html")

    print("\n" + "=" * 60)
    print(f"测试流程全部完成！")
    print(f"本次结果已存档至: {RUN_REPORT_DIR}")
    print(f"查看报告方式:")
    print(f"  方法1 : 在资源管理器中双击打开 -> {index_html_path}")
    print(f"  方法2 (命令行): allure open {HTML_DIR}")
    print("=" * 60)

if __name__ == "__main__":
    main()