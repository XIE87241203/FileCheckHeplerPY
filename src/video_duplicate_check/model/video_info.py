# -*- coding: utf-8 -*-
"""
@author: 视频信息
@time: 2024/05/17
"""
from typing import List, Optional

class VideoInfo:
    """
    存储视频信息的类。
    """
    def __init__(self, path: str, video_name: str, md5: str, alias: str, signatures: Optional[List[str]] = None, id: Optional[int] = None):
        """
        初始化视频信息对象。

        :param path: 视频文件的绝对路径。
        :param video_name: 视频文件名。
        :param md5: 视频文件的MD5哈希值。
        :param alias: 视频的别名，重复的视频将有同一个别名。
        :param signatures: (可选) 视频的感知哈希签名列表。
        :param id: (可选) 数据库中的ID。
        """
        self.id: Optional[int] = id
        self.path: str = path
        self.video_name: str = video_name
        self.md5: str = md5
        self.signatures: List[str] = signatures if signatures is not None else []
        self.alias: str = alias
