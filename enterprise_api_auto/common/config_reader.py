import yaml
import os
from typing import Dict, Any


class ConfigReader:
    """配置文件读取工具类，单例模式避免重复读取"""
    _instance = None
    _env_config: Dict[str, Any] = {}
    _api_config: Dict[str, Any] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            # 初始化读取配置文件
            cls._instance._load_env_config()
            cls._instance._load_api_config()
        return cls._instance


    def _load_env_config(self) -> None:
        """读取环境配置文件"""
        env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "env.yaml")
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                self._env_config = yaml.safe_load(f)
        except FileNotFoundError:
            raise Exception(f"环境配置文件不存在：{env_path}")
        except yaml.YAMLError as e:
            raise Exception(f"环境配置文件格式错误：{e}")

    def _load_api_config(self) -> None:
        """读取接口配置文件"""
        api_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "api_config.yaml")
        try:
            with open(api_path, "r", encoding="utf-8") as f:
                self._api_config = yaml.safe_load(f)
        except FileNotFoundError:
            raise Exception(f"接口配置文件不存在：{api_path}")
        except yaml.YAMLError as e:
            raise Exception(f"接口配置文件格式错误：{e}")

    def get_env_config(self, env: str = "test") -> Dict[str, Any]:
        """获取指定环境的配置（默认测试环境）"""
        if env not in self._env_config:
            raise Exception(f"不支持的环境：{env}，可选环境：{list(self._env_config.keys())}")
        return self._env_config[env]

    def get_api_path(self, api_key: str) -> str:
        """获取接口路径，支持多级key，格式："user.login" """
        keys = api_key.split(".")
        config = self._api_config
        try:
            for key in keys:
                config = config[key]
            return str(config)
        except KeyError:
            raise Exception(f"接口配置不存在：{api_key}")
