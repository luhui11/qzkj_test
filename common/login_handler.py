# common/login_handler.py
import requests


class LoginHandler:
    """
    统一登录处理类
    策略：API 登录获取 Token -> 注入浏览器 Context
    """

    def __init__(self):
        self.token = None
        self.cookies = {}
        # 从配置文件读取登录信息 (根据你的 yaml 结构调整 key)
        # 假设 env.yaml 或 api_config.yaml 中有 auth 部分
        try:
            # 这里需要根据你实际的 config_reader 实现来调整
            # 示例：直接硬编码或从 os.environ 获取
            self.account = "lh_nc"
            self.password = "Hello#777"
            self.login_url = "http://192.168.2.226:35200/dsp-api/api/qiz-dp-system/Login"  # 替换真实地址
        except Exception:
            pass

    def get_token_via_api(self):
        """调用登录接口获取 Token"""
        if self.token:
            return self.token

        payload = {
            "account": self.account,
            "password": self.password
        }

        try:
            # 直接使用 requests，或者调用你框架里的 http_client
            response = requests.post(self.login_url, json=payload)
            response.raise_for_status()
            data = response.json()

            # ⚠️ 关键：根据实际接口返回调整取值路径
            # 假设返回：{ "code": 200, "data": { "token": "xyz..." } }
            if data.get('code') == 200 or data.get('status') == 'success':
                self.token = data['data'].get('token') or data.get('token')
                print(f"✅ 登录成功，Token: {self.token[:10]}...")
                return self.token
            else:
                raise Exception(f"登录失败：{data}")
        except Exception as e:
            print(f"❌ 获取 Token 异常：{e}")
            raise e

    def inject_auth_to_context(self, context):
        """
        将登录态注入到 Playwright 的 browser context 中
        :param context: playwright.sync_api.BrowserContext
        """
        if not self.token:
            self.get_token_via_api()

        # 方式 A: 添加 Cookie (适用于 Cookie 认证)
        # 注意：Domain 必须与访问的网址匹配，否则无效
        context.add_cookies([
            {
                "name": "AUTH_TOKEN",  # ⚠️ 替换为后端实际要求的 Cookie 名称
                "value": self.token,
                "domain": "your-app.com",  # ⚠️ 替换为你的域名
                "path": "/"
            }
        ])

        # 方式 B: 注入 LocalStorage (适用于前端 JWT 存储，如 Vue/React)
        # 这需要在页面加载前或加载初期执行
        context.add_init_script(f"""
            window.localStorage.setItem('auth_token', '{self.token}');
            // 如果有其他用户信息需要模拟，也可以在这里塞入
        """)

        print("认证信息已注入浏览器上下文")
