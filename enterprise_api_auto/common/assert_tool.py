import json
from typing import Dict, Any, Optional
from log_handler import logger

class AssertTool:
    """自定义断言工具类，封装常用断言场景，提供详细日志"""

    @staticmethod
    def assert_code(response, expected_code: int = 200) -> None:
        """断言响应状态码"""
        actual_code = response.status_code
        try:
            assert actual_code == expected_code
            logger.info(f"状态码断言成功：预期{expected_code}，实际{actual_code}")
        except AssertionError:
            logger.error(f"状态码断言失败：预期{expected_code}，实际{actual_code}")
            raise

    @staticmethod
    def assert_json_key(response, expected_key: str) -> None:
        """断言响应json中包含指定key（支持多级key，格式："data.user.id"）"""
        try:
            response_json = response.json()
            keys = expected_key.split(".")
            value = response_json
            for key in keys:
                value = value[key]
            logger.info(f"JSON Key断言成功：响应中包含key「{expected_key}」，值为「{value}」")
        except (KeyError, json.JSONDecodeError) as e:
            logger.error(f"JSON Key断言失败：响应中不包含key「{expected_key}」，异常信息：{str(e)}")
            raise

    @staticmethod
    def assert_json_value(response, expected_key: str, expected_value: Any) -> None:
        """断言响应json中指定key的取值符合预期"""
        try:
            response_json = response.json()
            keys = expected_key.split(".")
            value = response_json
            for key in keys:
                value = value[key]
            assert value == expected_value
            logger.info(f"JSON Value断言成功：key「{expected_key}」预期{expected_value}，实际{value}")
        except (KeyError, json.JSONDecodeError, AssertionError) as e:
            logger.error(f"JSON Value断言失败：key「{expected_key}」预期{expected_value}，异常信息：{str(e)}")
            raise

    @staticmethod
    def assert_response_not_empty(response) -> None:
        """断言响应内容非空"""
        try:
            assert len(response.text) > 0
            logger.info("响应内容非空断言成功")
        except AssertionError:
            logger.error("响应内容非空断言失败：响应内容为空")
            raise
