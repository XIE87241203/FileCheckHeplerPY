# -*- coding: utf-8 -*-
"""
@author: 视频信息缓存存储器
@time: 2024/05/17
"""
import sqlite3
from typing import List, Optional

from src.video_duplicate_check.model.video_info import VideoInfo
from src.video_duplicate_check.storage.db_helper import DBHelper


class VideoInfoCacheStorage:
    """
    管理视频信息缓存，用于存储和检索 VideoInfo 对象。

    此类通过 DBHelper 进行数据库操作，并支持 'with' 语句自动管理数据库连接。
    """

    def __init__(self, db_dir: str = 'db'):
        """
        初始化视频信息缓存存储器。

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

    def add_video_info(self, video_info: VideoInfo):
        """
        将一个 VideoInfo 对象添加到缓存中。

        如果缓存中已存在相同路径的视频信息，则会更新它；否则，插入新记录。
        操作完成后，VideoInfo 对象的 id 属性会被更新。

        :param video_info: 要缓存的 VideoInfo 对象。
        """
        if not self.conn:
            raise ConnectionError("数据库未连接。请在操作前调用 connect() 或使用 'with' 语句。")

        cursor = self.conn.cursor()
        signatures_str = ",".join(video_info.signatures) if video_info.signatures else ""

        # 检查路径是否存在
        cursor.execute(f"SELECT id FROM {self.db_helper.TABLE_VIDEO_INFO_CACHE} WHERE path = ?", (video_info.path,))
        result = cursor.fetchone()

        if result:
            # 更新现有记录
            existing_id = result[0]
            video_info.id = existing_id
            cursor.execute(f"""
                UPDATE {self.db_helper.TABLE_VIDEO_INFO_CACHE}
                SET video_name = ?, md5 = ?, signatures = ?, alias = ?
                WHERE id = ?
            """, (video_info.video_name, video_info.md5, signatures_str, video_info.alias, existing_id))
        else:
            # 插入新记录
            cursor.execute(f"""
                INSERT INTO {self.db_helper.TABLE_VIDEO_INFO_CACHE} (path, video_name, md5, signatures, alias)
                VALUES (?, ?, ?, ?, ?)
            """, (video_info.path, video_info.video_name, video_info.md5, signatures_str, video_info.alias))
            video_info.id = cursor.lastrowid  # 获取新ID

        self.conn.commit()

    def get_video_info_by_path(self, path: str) -> Optional[VideoInfo]:
        """
        根据文件路径从缓存中检索 VideoInfo 对象。

        :param path: 视频文件的绝对路径。
        :return: 如果找到，则返回 VideoInfo 对象；否则返回 None。
        """
        if not self.conn:
            raise ConnectionError("数据库未连接。请在操作前调用 connect() 或使用 'with' 语句。")

        cursor = self.conn.cursor()
        cursor.execute(f"SELECT id, path, video_name, md5, signatures, alias FROM {self.db_helper.TABLE_VIDEO_INFO_CACHE} WHERE path = ?", (path,))
        result = cursor.fetchone()

        if result:
            id, path, video_name, md5, signatures_str, alias = result
            signatures = signatures_str.split(',') if signatures_str else []
            return VideoInfo(id=id, path=path, video_name=video_name, md5=md5, signatures=signatures, alias=alias)

        return None

    def get_video_info_by_name(self, video_name: str) -> Optional[VideoInfo]:
        """
        根据文件名从缓存中检索 VideoInfo 对象。

        :param video_name: 视频文件名。
        :return: 如果找到，则返回 VideoInfo 对象；否则返回 None。
        """
        if not self.conn:
            raise ConnectionError("数据库未连接。请在操作前调用 connect() 或使用 'with' 语句。")

        cursor = self.conn.cursor()
        cursor.execute(f"SELECT id, path, video_name, md5, signatures, alias FROM {self.db_helper.TABLE_VIDEO_INFO_CACHE} WHERE video_name = ?", (video_name,))
        result = cursor.fetchone()

        if result:
            id, path, video_name, md5, signatures_str, alias = result
            signatures = signatures_str.split(',') if signatures_str else []
            return VideoInfo(id=id, path=path, video_name=video_name, md5=md5, signatures=signatures, alias=alias)

        return None

    def get_video_info_by_md5(self, md5: str) -> Optional[VideoInfo]:
        """
        根据MD5值从缓存中检索第一个匹配的VideoInfo对象。

        :param md5: 视频的MD5哈希值。
        :return: 如果找到，则返回VideoInfo对象；否则返回None。
        """
        if not self.conn:
            raise ConnectionError("数据库未连接。请在操作前调用 connect() 或使用 'with' 语句。")

        cursor = self.conn.cursor()
        cursor.execute(f"SELECT id, path, video_name, md5, signatures, alias FROM {self.db_helper.TABLE_VIDEO_INFO_CACHE} WHERE md5 = ?", (md5,))
        result = cursor.fetchone()

        if result:
            id, path, video_name, db_md5, signatures_str, alias = result
            signatures = signatures_str.split(',') if signatures_str else []
            return VideoInfo(id=id, path=path, video_name=video_name, md5=db_md5, signatures=signatures, alias=alias)

        return None

    def get_video_info_by_alias(self, alias: str) -> List[VideoInfo]:
        """
        根据别名(alias)从缓存中检索所有匹配的VideoInfo对象。

        :param alias: 视频的别名。
        :return: 匹配的VideoInfo对象列表。
        """
        if not self.conn:
            raise ConnectionError("数据库未连接。请在操作前调用 connect() 或使用 'with' 语句。")

        cursor = self.conn.cursor()
        cursor.execute(f"SELECT id, path, video_name, md5, signatures, alias FROM {self.db_helper.TABLE_VIDEO_INFO_CACHE} WHERE alias = ?", (alias,))
        results = cursor.fetchall()

        video_infos = []
        for row in results:
            id, path, video_name, md5, signatures_str, db_alias = row
            signatures = signatures_str.split(',') if signatures_str else []
            video_infos.append(VideoInfo(id=id, path=path, video_name=video_name, md5=md5, signatures=signatures, alias=db_alias))

        return video_infos

    def get_all_video_infos(self) -> List[VideoInfo]:
        """
        从缓存中检索所有的 VideoInfo 对象。

        :return: 缓存中所有 VideoInfo 对象的列表。
        """
        if not self.conn:
            raise ConnectionError("数据库未连接。请在操作前调用 connect() 或使用 'with' 语句。")

        cursor = self.conn.cursor()
        cursor.execute(f"SELECT id, path, video_name, md5, signatures, alias FROM {self.db_helper.TABLE_VIDEO_INFO_CACHE}")
        results = cursor.fetchall()

        video_infos = []
        for row in results:
            id, path, video_name, md5, signatures_str, alias = row
            signatures = signatures_str.split(',') if signatures_str else []
            video_infos.append(VideoInfo(id=id, path=path, video_name=video_name, md5=md5, signatures=signatures, alias=alias))

        return video_infos

    def clear_cache(self):
        """
        清空 `video_info_cache` 表中的所有数据。
        """
        if not self.conn:
            raise ConnectionError("数据库未连接。请在操作前调用 connect() 或使用 'with' 语句。")

        cursor = self.conn.cursor()
        cursor.execute(f"DELETE FROM {self.db_helper.TABLE_VIDEO_INFO_CACHE}")
        self.conn.commit()
