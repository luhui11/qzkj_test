import logging
import os
from datetime import datetime
from common.config_reader import ConfigReader

class LogHandler:
    """日志处理工具类，统一日志格式和存储"""
    _logger = None

    @classmethod
    def get_logger(cls) -> logging.Logger:
        if cls._logger is None:
            # 1. 初始化logger
            cls._logger = logging.getLogger("EnterpriseApiAuto")
            cls._logger.setLevel(logging.DEBUG)  # 根日志级别（最低）

            # 2. 定义日志格式
            log_format = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            )

            # 3. 创建日志目录（若不存在）
            log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "log")
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)

            # 4. 文件处理器（按日期生成日志文件）
            log_file = os.path.join(log_dir, f"api_auto_{datetime.now().strftime('%Y%m%d')}.log")
            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_handler.setLevel(logging.INFO)  # 文件日志级别（INFO及以上）
            file_handler.setFormatter(log_format)

            # 5. 控制台处理器（便于调试）
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.DEBUG)  # 控制台日志级别（DEBUG及以上）
            console_handler.setFormatter(log_format)

            # 6. 添加处理器到logger
            cls._logger.addHandler(file_handler)
            cls._logger.addHandler(console_handler)

        return cls._logger

# 全局日志实例，便于其他模块直接调用
logger = LogHandler.get_logger()
