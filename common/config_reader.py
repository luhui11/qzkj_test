import yaml
import os
from typing import Dict, Any

class ConfigReader:
    """配置文件读取工具类，单例模式避免重复读取"""
    _instance = None
    _env_config: Dict[str, Any] = {}
    _api_config: Dict[str, Any] = {}
    _raw_config: Dict[str, Any] = {}  # 补充这个属性，防止下面代码报错

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            # 初始化读取配置文件
            cls._instance._load_env_config()
            cls._instance._load_api_config()
        return cls._instance

    def _load_env_config(self) -> None:
        """读取环境配置文件"""
        # ✅ 修复：在函数内部导入 logger
        from log_handler import logger

        env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "env.yaml")
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                self._env_config = yaml.safe_load(f)
                # 假设 env.yaml 的结构里包含 active_env 和 environments
                # 如果 env.yaml 结构不同，请根据实际情况调整
                self._raw_config = self._env_config
        except FileNotFoundError:
            logger.error(f"环境配置文件不存在：{env_path}")
            raise Exception(f"环境配置文件不存在：{env_path}")
        except yaml.YAMLError as e:
            logger.error(f"环境配置文件格式错误：{e}")
            raise Exception(f"环境配置文件格式错误：{e}")

    def _load_api_config(self) -> None:
        """读取接口配置文件"""
        # ✅ 修复：在函数内部导入 logger
        from log_handler import logger

        api_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "api_config.yaml")
        try:
            with open(api_path, "r", encoding="utf-8") as f:
                self._api_config = yaml.safe_load(f)
        except FileNotFoundError:
            logger.error(f"接口配置文件不存在：{api_path}")
            raise Exception(f"接口配置文件不存在：{api_path}")
        except yaml.YAMLError as e:
            logger.error(f"接口配置文件格式错误：{e}")
            raise Exception(f"接口配置文件格式错误：{e}")

    def get_env_config(self, env: str = None) -> Dict[str, Any]:
        """
        获取指定环境的配置
        如果 env 为 None，自动使用 active_env
        """
        # ✅ 修复：在函数内部导入 logger
        from log_handler import logger

        # 1. 确定要使用的环境名
        if env is None:
            # 👇 关键修复：从配置中读取 active_env
            # 注意：确保 self._raw_config 已经在 _load_env_config 中被正确赋值
            if not self._raw_config:
                # 如果还没加载，尝试重新加载或报错
                self._load_env_config()

            env = self._raw_config.get("active_env")
            if not env:
                raise ValueError("配置文件中未定义 'active_env' 且未传入 env 参数")
            logger.info(f"未指定环境，使用 active_env: {env}")

        # 2. 获取 environments 字典
        environments = self._raw_config.get("environments")
        if not environments:
            raise ValueError("配置文件中未定义 'environments' 节点")

        # 3. 查找具体环境
        if env not in environments:
            available_envs = list(environments.keys())
            raise ValueError(f"不支持的环境：'{env}'。可选环境：{available_envs}")

        logger.info(f"成功获取环境配置：{env}")
        return environments[env]

    def get_api_path(self, api_key: str) -> str:
        """获取接口路径，支持多级 key，格式："user.login" """
        # ✅ 修复：在函数内部导入 logger (如果需要记录错误日志)
        from log_handler import logger

        keys = api_key.split(".")
        config = self._api_config
        try:
            for key in keys:
                config = config[key]
            return str(config)
        except KeyError:
            logger.error(f"接口配置不存在：{api_key}")
            raise Exception(f"接口配置不存在：{api_key}")