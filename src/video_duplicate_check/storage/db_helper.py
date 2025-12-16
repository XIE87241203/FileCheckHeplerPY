# -*- coding: utf-8 -*-
"""
@author: 数据库辅助类
@time: 2024/05/17
"""
import sqlite3
import os
import threading


class DBHelper:
    """
    数据库辅助类，用于封装数据库连接和表创建（单例模式）。
    """
    _instance = None
    _lock = threading.Lock()

    # 数据库文件名
    DB_NAME = 'fileCheckHelper.db'
    # 数据库版本，用于数据库迁移
    DB_VERSION = 1
    # 视频特征表
    TABLE_VIDEO_FEATURES = 'video_features'
    # 视频信息缓存表
    TABLE_VIDEO_INFO_CACHE = 'video_info_cache'

    def __new__(cls, *args, **kwargs):
        """
        实现线程安全的单例模式，确保全局只有一个DBHelper实例。

        :param args: 位置参数。
        :param kwargs: 关键字参数。
        :return: DBHelper的单例实例。
        """
        if not cls._instance:
            with cls._lock:
                # 再次检查，防止多线程环境下重复创建实例
                if not cls._instance:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, db_dir: str = 'db'):
        """
        初始化数据库辅助类。
        由于是单例，此构造方法仅在第一次实例化时执行一次。

        :param db_dir: 数据库文件所在的目录，默认为 'db'。
        """
        # 防止重复初始化
        if hasattr(self, '_initialized'):
            return

        base_dir = os.getcwd()
        db_path = os.path.join(base_dir, db_dir, self.DB_NAME)
        self.db_path = db_path
        # 确保数据库文件所在的目录存在
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        # 初始化时创建或更新表
        self._create_or_update_tables()
        self._initialized = True

    def _create_or_update_tables(self):
        """
        创建或更新数据库表结构，并根据DB_VERSION进行版本适配。
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # 获取当前数据库版本
            cursor.execute("PRAGMA user_version")
            current_version = cursor.fetchone()[0]

            # 仅在需要时进行基础表创建
            self._create_base_tables(cursor)

            # --- 数据库版本迁移 --- #
            self._update_db(self, current_version)
            # if current_version < 1:
            # 版本 1 迁移：为 video_info_cache 表添加 alias 列

            # --- 迁移结束 --- #

            # 如果版本已更新，则设置新的数据库版本
            if current_version != self.DB_VERSION:
                cursor.execute(f"PRAGMA user_version = {self.DB_VERSION}")

            conn.commit()

    def _update_db(self, old_version, new_version=DB_VERSION):
        return

    def _create_base_tables(self, cursor):
        """
        创建项目所需的基础数据表，如果表不存在的话。

        :param cursor: 数据库游标。
        """
        # 创建 video_features 表
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS {self.TABLE_VIDEO_FEATURES} (
                md5 TEXT PRIMARY KEY NOT NULL,
                signature TEXT NOT NULL,
                alias TEXT NOT NULL
            )
        ''')
        # 创建 video_info_cache 表
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS {self.TABLE_VIDEO_INFO_CACHE} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT NOT NULL UNIQUE,
                video_name TEXT NOT NULL,
                md5 TEXT NOT NULL,
                signatures TEXT
            )
        ''')

    def get_connection(self) -> sqlite3.Connection:
        """
        获取一个新的数据库连接。

        :return: 数据库连接对象。
        """
        return sqlite3.connect(self.db_path)

    def close_connection(self, conn: sqlite3.Connection):
        """
        关闭一个数据库连接。

        :param conn: 要关闭的数据库连接对象。
        """
        if conn:
            conn.close()
