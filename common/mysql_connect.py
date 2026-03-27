import os
import mysql.connector
from mysql.connector import pooling, Error

# 1. 配置读取 (带默认值，防止环境变量缺失导致报错)
# 注意：生产环境中请确保环境变量已设置，不要依赖这里的默认值
DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER",),
    "password": os.getenv("DB_PASSWORD"),  # 密码不能随便给默认值，这里留空会报错提醒
    "database": os.getenv("DB_NAME"),
    "port": int(os.getenv("DB_PORT", "8306")),  # 建议用环境变量控制端口，默认3306
}


class DatabasePool:
    _pool = None
    @classmethod
    def get_pool(cls):
        """获取连接池单例"""
        if cls._pool is None:
            try:
                print(f"正在初始化连接池 (Host: {DB_CONFIG['host']}, DB: {DB_CONFIG['database']})...")
                cls._pool = pooling.MySQLConnectionPool(
                    pool_name="mypool",
                    pool_size=10,  # 池中保持的连接数
                    pool_reset_session=True,  # 归还连接时重置状态（防止事务未提交等污染）
                    **DB_CONFIG
                )
                print("✅ 连接池初始化成功")
            except Error as e:
                print(f"❌ 连接池初始化失败: {e}")
                raise e
        return cls._pool

    @classmethod
    def get_connection(cls):
        """从池中获取一个连接"""
        try:
            return cls.get_pool().get_connection()
        except Error as e:
            print(f"❌ 获取连接失败: {e}")
            raise

