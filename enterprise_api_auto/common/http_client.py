import requests
from typing import Dict, Any, Optional
from requests import Response
from tenacity import retry, stop_after_attempt, wait_exponential
from common.config_reader import ConfigReader
from common.log_handler import logger

class HttpClient:
    """HTTP请求封装类，支持所有HTTP方法、超时、重试、会话保持"""
    def __init__(self, env: str = "test"):
        self.config_reader = ConfigReader()
        self.env_config = self.config_reader.get_env_config(env)
        self.base_url = self.env_config["base_url"]
        self.timeout = self.env_config["timeout"]
        self.retry_times = self.env_config["retry_times"]
        # 会话保持（用于需要登录后维持cookie/token的场景）
        self.session = requests.Session()

    def _get_full_url(self, api_path: str) -> str:
        """拼接完整接口地址"""
        return f"{self.base_url}{api_path}"

    @retry(
        stop=stop_after_attempt(3),  # 最大重试次数（优先取环境配置，默认3次）
        wait=wait_exponential(multiplier=1, min=2, max=5),  # 等待策略：2^n秒，最小2s，最大5s
        reraise=True
    )
    def _send_request(self, method: str, api_path: str, **kwargs) -> Response:
        """
        内部请求发送方法，封装重试逻辑
        :param method: HTTP方法（get/post/put/delete）
        :param api_path: 接口路径（可直接传路径或api_config中的key）
        :param kwargs: requests额外参数（params/data/json/headers等）
        :return: Response对象
        """
        # 处理接口路径（支持直接传路径或api_config的key，如"user.login"）
        if not api_path.startswith("/"):
            api_path = self.config_reader.get_api_path(api_path)
        full_url = self._get_full_url(api_path)

        # 设置默认超时
        if "timeout" not in kwargs:
            kwargs["timeout"] = self.timeout

        try:
            logger.info(f"发送{method.upper()}请求：{full_url}")
            logger.info(f"请求参数：{kwargs}")
            response = self.session.request(method, full_url, **kwargs)
            logger.info(f"响应状态码：{response.status_code}")
            logger.info(f"响应内容：{response.text}")
            return response
        except requests.exceptions.Timeout:
            logger.error(f"请求超时：{full_url}，超时时间：{self.timeout}s")
            raise
        except requests.exceptions.ConnectionError:
            logger.error(f"连接失败：{full_url}")
            raise
        except Exception as e:
            logger.error(f"请求异常：{full_url}，异常信息：{str(e)}")
            raise

    def get(self, api_path: str, params: Optional[Dict[str, Any]] = None,
            headers: Optional[Dict[str, Any]] = None, **kwargs) -> Response:
        """GET请求封装"""
        return self._send_request("get", api_path, params=params, headers=headers, **kwargs)

    def post(self, api_path: str, data: Optional[Dict[str, Any]] = None,
             json: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, Any]] = None,
             **kwargs) -> Response:
        """POST请求封装（支持form-data和json格式）"""
        return self._send_request("post", api_path, data=data, json=json, headers=headers, **kwargs)

    def put(self, api_path: str, data: Optional[Dict[str, Any]] = None,
            json: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, Any]] = None,
            **kwargs) -> Response:
        """PUT请求封装"""
        return self._send_request("put", api_path, data=data, json=json, headers=headers, **kwargs)

    def delete(self, api_path: str, params: Optional[Dict[str, Any]] = None,
               headers: Optional[Dict[str, Any]] = None, **kwargs) -> Response:
        """DELETE请求封装"""
        return self._send_request("delete", api_path, params=params, headers=headers, **kwargs)

    def close_session(self) -> None:
        """关闭会话"""
        self.session.close()
        logger.info("HTTP会话已关闭")
