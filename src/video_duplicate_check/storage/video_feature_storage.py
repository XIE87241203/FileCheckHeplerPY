# -*- coding: utf-8 -*-
"""
@author: 视频特征存储器
@time: 2024/05/17
"""
import sqlite3
from typing import List

from src.video_duplicate_check.storage.db_helper import DBHelper


class VideoFeatureStorage:
    """
    管理视频特征数据库，用于存储和检索视频的MD5和感知哈希签名。

    此类通过 DBHelper 进行数据库操作，并支持 'with' 语句自动管理数据库连接。
    """

    def __init__(self, db_dir: str = 'db'):
        """
        初始化视频特征存储器。

        :param db_dir: 数据库文件所在的目录，默认为 'db'。
        """
        self.db_helper = DBHelper(db_dir)
        self.conn: sqlite3.Connection | None = None

    def __enter__(self):
        """
        实现上下文管理器协议的 enter 方法，用于支持 'with' 语句。
        """
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        实现上下文管理器协议的 exit 方法，用于支持 'with' 语句。
        """
        self.db_helper.close_connection(self.conn)
        self.conn = None

    def connect(self):
        """
        连接到SQLite数据库。
        """
        if self.conn is None:
            self.conn = self.db_helper.get_connection()

    def add_feature(self, md5: str, signature: str):
        """
        向指定MD5的视频添加一个签名。

        如果MD5不存在，则创建新条目；如果已存在，则追加新签名（如果签名不存在）。

        :param md5: 视频的MD5哈希值。
        :param signature: 视频的一个感知哈希签名。
        """
        if not self.conn:
            raise ConnectionError("数据库未连接。请在操作前调用 connect() 或使用 'with' 语句。")

        cursor = self.conn.cursor()
        cursor.execute(f"SELECT signature FROM {self.db_helper.TABLE_VIDEO_FEATURES} WHERE md5 = ?", (md5,))
        result = cursor.fetchone()

        if result:
            existing_signatures = result[0].split(',')
            if signature not in existing_signatures:
                all_signatures = existing_signatures + [signature]
                signature_str = ",".join(sorted(all_signatures))
                cursor.execute(f"UPDATE {self.db_helper.TABLE_VIDEO_FEATURES} SET signature = ? WHERE md5 = ?", (signature_str, md5))
        else:
            cursor.execute(f"INSERT INTO {self.db_helper.TABLE_VIDEO_FEATURES} (md5, signature) VALUES (?, ?)", (md5, signature))

        self.conn.commit()

    def add_features(self, md5: str, signatures: List[str]):
        """
        向指定MD5的视频批量添加多个签名。

        如果MD5不存在，则创建新条目；如果已存在，则仅添加不重复的新签名。

        :param md5: 视频的MD5值。
        :param signatures: 视频的签名列表。
        """
        if not self.conn:
            raise ConnectionError("数据库未连接。请在操作前调用 connect() 或使用 'with' 语句。")

        cursor = self.conn.cursor()
        cursor.execute(f"SELECT signature FROM {self.db_helper.TABLE_VIDEO_FEATURES} WHERE md5 = ?", (md5,))
        result = cursor.fetchone()
        unique_new_signatures = sorted(list(set(signatures)))

        if result:
            existing_signatures_set = set(result[0].split(','))
            all_signatures_set = existing_signatures_set.union(set(unique_new_signatures))
            signature_str = ",".join(sorted(list(all_signatures_set)))
            cursor.execute(f"UPDATE {self.db_helper.TABLE_VIDEO_FEATURES} SET signature = ? WHERE md5 = ?", (signature_str, md5))
        else:
            signature_str = ",".join(unique_new_signatures)
            cursor.execute(f"INSERT INTO {self.db_helper.TABLE_VIDEO_FEATURES} (md5, signature) VALUES (?, ?)", (md5, signature_str))

        self.conn.commit()

    def get_signatures(self, md5: str) -> List[str]:
        """
        根据MD5值从数据库中检索所有关联的签名。

        :param md5: 视频的MD5哈希值。
        :return: 与MD5关联的签名列表，如果不存在则返回空列表。
        """
        if not self.conn:
            raise ConnectionError("数据库未连接。请在操作前调用 connect() 或使用 'with' 语句。")

        cursor = self.conn.cursor()
        cursor.execute(f"SELECT signature FROM {self.db_helper.TABLE_VIDEO_FEATURES} WHERE md5 = ?", (md5,))
        result = cursor.fetchone()

        return result[0].split(',') if result and result[0] else []

    def clear_features(self):
        """
        清空 `video_features` 表中的所有数据。
        """
        if not self.conn:
            raise ConnectionError("数据库未连接。请在操作前调用 connect() 或使用 'with' 语句。")

        cursor = self.conn.cursor()
        cursor.execute(f"DELETE FROM {self.db_helper.TABLE_VIDEO_FEATURES}")
        self.conn.commit()
