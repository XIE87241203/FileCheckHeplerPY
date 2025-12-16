# -*- coding: utf-8 -*-
"""
@author: MD5校验工具
@time: 2024/05/17
"""
import hashlib

class MD5Helper:
    """
    MD5校验工具类，用于计算文件的MD5值。
    """

    @staticmethod
    def calculate_md5(file_path: str) -> str:
        """
        计算文件的MD5哈希值。

        通过逐块读取文件内容，计算其MD5值，适用于大文件，可避免一次性加载整个文件到内存中。

        :param file_path: 文件的路径。
        :return: 文件的MD5哈希值（以十六进制字符串形式表示）。
        :raises FileNotFoundError: 如果指定的文件路径不存在。
        """
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except FileNotFoundError:
            raise FileNotFoundError(f"文件未找到: {file_path}")
