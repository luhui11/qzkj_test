# common/http_client.py
import requests
from typing import Optional, Dict, Any
from common.log_handler import logger
from common.config_reader import ConfigReader


class HttpClient:
    def __init__(self, base_url: str = None):
        self.session = requests.Session()

        # 默认基础头 (会在 test 中被覆盖，但保留作为兜底)
        self.session.headers.update({
            'User-Agent': 'EnterpriseApiAuto/1.0',
        })

        config_reader = ConfigReader()
        env_config = config_reader.get_env_config()
        self.base_url = base_url or env_config.get("base_url")

        logger.info(f"HttpClient 初始化成功 | BaseURL: {self.base_url}")

    def set_auth_token(self, token: str):
        """设置或移除 Authorization 头"""
        if token and str(token).strip():
            self.session.headers['Authorization'] = f'Bearer {token}'
            logger.debug(f"设置 Token: Bearer {token[:10]}...")
        else:
            self.session.headers.pop('Authorization', None)
            logger.debug("移除 Token")

    def post(self, url: str, json: Optional[Dict[str, Any]] = None, data: Optional[Dict[str, Any]] = None,
             **kwargs) -> requests.Response:
        """
        发送 POST 请求
        :param url: 接口路径
        :param json: JSON 数据 (自动设 Content-Type: application/json)
        :param data: 表单数据 (自动设 Content-Type: application/x-www-form-urlencoded)
        """
        full_url = f"{self.base_url}{url}"

        # 记录调试信息
        logger.debug(f"发送 POST: {full_url}")
        logger.debug(f"Headers: {dict(self.session.headers)}")

        if data is not None:
            logger.debug(f"Body (Form): {data}")
            # 使用 data= 发送表单
            response = self.session.post(full_url, data=data, **kwargs)
        elif json is not None:
            logger.debug(f"Body (JSON): {json}")
            # 使用 json= 发送 JSON
            response = self.session.post(full_url, json=json, **kwargs)
        else:
            response = self.session.post(full_url, **kwargs)

        logger.debug(f"状态码：{response.status_code}")
        logger.debug(f"响应内容：{response.text[:500]}")  # 防止日志过长

        return response

    def get(self, url: str, **kwargs) -> requests.Response:
        full_url = f"{self.base_url}{url}"
        logger.debug(f"发送 GET: {full_url}")
        response = self.session.get(full_url, **kwargs)
        logger.debug(f"状态码：{response.status_code}")
        return response