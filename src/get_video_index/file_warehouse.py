import os
from collections import defaultdict
from src.utils.log_utils import logger


class FileWarehouse:
    """
    一个用于在指定目录中扫描视频文件的仓库类。
    """

    # 定义一个包含常见视频文件扩展名的集合，使用集合（set）可以提高查找效率。
    _VIDEO_FORMATS = {
        ".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm", ".mpeg",
        ".mpg", ".3gp", ".m4v", ".ogg", ".vob", ".ts", ".rmvb", ".m2ts",
    }

    def __init__(self, dir_path_list):
        """
        构造函数，用于初始化文件仓库。

        :param dir_path_list: 需要扫描的目录路径列表。
        """
        # 保存需要扫描的目录列表
        self.dir_path_list = dir_path_list
        # 初始化一个默认字典（defaultdict）。当访问一个不存在的键时，会自动创建一个空列表作为默认值。
        # 这简化了后续添加文件路径的代码。
        self.video_map = defaultdict(list)

    def _is_video_file(self, file_name):
        """
        通过检查文件扩展名来判断一个文件是否为视频文件。

        :param file_name: 要检查的文件名。
        :return: 如果是视频文件则返回 True，否则返回 False。
        """
        # os.path.splitext() 用于分离文件名和扩展名，例如 "video.mp4" -> ("video", ".mp4")
        _, ext = os.path.splitext(file_name)
        # 将扩展名转换为小写进行比较，以实现不区分大小写的检查。
        return ext.lower() in self._VIDEO_FORMATS

    def _find_videos_in_dir(self, root_dir):
        """
        在单个根目录及其所有子目录中递归查找视频文件，并更新 video_map。

        :param root_dir: 要查找的根目录。
        """
        # os.walk() 会递归地遍历指定目录下的所有子文件夹和文件。
        # root: 当前正在遍历的目录路径。
        # files: 当前目录下的文件列表。
        for root, _, files in os.walk(root_dir):
            # 遍历当前目录下的所有文件
            for file in files:
                # 检查文件是否为视频格式
                if self._is_video_file(file):
                    # 组合路径和文件名
                    full_path = os.path.join(root, file)
                    # 获取绝对路径，确保路径的规范性
                    abs_path = os.path.abspath(full_path)
                    # 将文件名作为键，文件的绝对路径添加到对应的值（列表）中
                    self.video_map[file].append(abs_path)

    def scan_videos(self):
        """
        扫描构造函数中提供的所有目录，收集所有视频文件的路径。

        :return: 一个字典，键是视频文件名，值是包含该文件所有绝对路径的列表。
        """
        # 使用 enumerate() 遍历目录列表，同时获取索引和值，用于打印进度。start=1 表示索引从1开始。
        for i, directory in enumerate(self.dir_path_list, 1):
            # 打印当前扫描的目录和进度
            logger.info(f'正在读取 "{directory}" 中，进度：{i}/{len(self.dir_path_list)}', self)
            # 调用内部方法来查找并记录该目录下的所有视频文件
            self._find_videos_in_dir(directory)
        # 返回最终收集到的包含所有视频文件信息的字典
        return self.video_map
