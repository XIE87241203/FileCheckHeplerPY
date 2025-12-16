# -*- coding: utf-8 -*-
"""
@author: 文件校验工具
@time: 2024/05/16
"""
import os
import subprocess
import io
from typing import List, Dict, Set, Optional

# Pillow and imagehash are required, please install them:
# pip install Pillow imagehash
from PIL import Image
import imagehash

from src.video_duplicate_check.utils.md5_helper import MD5Helper
from src.video_duplicate_check.model.video_info import VideoInfo
from src.video_duplicate_check.storage.video_feature_storage import VideoFeatureStorage
from src.video_duplicate_check.storage.video_info_cache_storage import VideoInfoCacheStorage
from src.utils.log_utils import LogUtils


class VideoDuplicateChecker:
    """
    视频查重器，通过ffmpeg提取视频帧并计算图像哈希值进行比较。
    """

    def __init__(self, ffmpeg_dir='ffmpeg', similarity_threshold: int = 5):
        """
        初始化视频查重器。

        :param ffmpeg_dir: ffmpeg的可执行文件所在目录。
        :param similarity_threshold: 图像哈希的相似度阈值，用于判断视频帧是否相似。
        """
        # 根据操作系统确定可执行文件名
        ffmpeg_exe = 'ffmpeg.exe' if os.name == 'nt' else 'ffmpeg'
        ffprobe_exe = 'ffprobe.exe' if os.name == 'nt' else 'ffprobe'

        # 获取当前工作目录，并拼接ffmpeg和ffprobe的完整路径
        base_dir = os.getcwd()
        self.ffmpeg_path = os.path.join(base_dir, ffmpeg_dir, 'bin', ffmpeg_exe)
        self.ffprobe_path = os.path.join(base_dir, ffmpeg_dir, 'bin', ffprobe_exe)
        self.similarity_threshold = similarity_threshold

        # 检查ffmpeg和ffprobe是否存在，如果不存在则抛出异常
        if not os.path.exists(self.ffmpeg_path) or not os.path.exists(self.ffprobe_path):
            raise FileNotFoundError(f"未在“{os.path.join(base_dir, ffmpeg_dir, 'bin')}”目录中找到ffmpeg或ffprobe。")
        
        # 初始化视频特征存储器和视频信息缓存
        self.feature_storage = VideoFeatureStorage()
        self.cache_storage = VideoInfoCacheStorage()
        self.log_utils = LogUtils()

    def _get_video_duration(self, video_path: str) -> float:
        """
        使用ffprobe获取视频的时长。

        :param video_path: 视频文件的路径。
        :return: 视频的时长（秒）。
        """
        # 构建ffprobe命令以获取视频时长
        command = [
            self.ffprobe_path,
            '-v', 'error',                      # 只输出错误信息
            '-show_entries', 'format=duration', # 显示格式信息中的时长
            '-of', 'default=noprint_wrappers=1:nokey=1', # 设置输出格式，不带键
            video_path
        ]
        # 执行命令并捕获标准输出
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        # 将输出转换为浮点数并返回
        return float(result.stdout.strip())

    def _generate_video_signatures(self, video_path: str, precision: int) -> List[str]:
        """
        为视频文件生成感知哈希签名。

        :param video_path: 视频文件的路径。
        :param precision: 截图的精度，即从视频中提取的帧数。
        :return: 视频的签名列表。
        """
        self.log_utils.log(LogUtils.LOG_LEVEL_INFO, f"正在为 {os.path.basename(video_path)} 生成签名...")
        duration = self._get_video_duration(video_path)
        new_signatures = []

        # 根据精度，在视频不同时间点截图并计算哈希值
        for i in range(1, precision + 1):
            timestamp = (i / (precision + 1)) * duration
            command = [
                self.ffmpeg_path, '-ss', str(timestamp), '-i', video_path,
                '-vframes', '1', '-f', 'image2pipe', '-c:v', 'png', '-'
            ]
            proc = subprocess.run(command, capture_output=True, check=True, timeout=10)
            image = Image.open(io.BytesIO(proc.stdout))
            new_signatures.append(str(imagehash.phash(image)))
        
        self.log_utils.log(LogUtils.LOG_LEVEL_INFO, "签名生成完毕。")
        return new_signatures

    def _get_video_info(self, video_path: str, precision: int) -> Optional[VideoInfo]:
        """
        获取或创建视频文件的VideoInfo对象。

        该方法首先计算视频的MD5，然后检查数据库中是否已存在该视频的签名。
        如果签名不存在，则调用 _generate_video_signatures 生成新签名并存入数据库。
        之后，它会检查缓存中是否有同名或同MD5的文件，以复用别名(alias)。
        最后，创建VideoInfo对象并存入缓存。

        :param video_path: 视频文件的路径。
        :param precision: 截图的精度，即从视频中提取的帧数。
        :return: 包含视频信息的VideoInfo对象；如果处理失败，则返回None。
        """
        if not os.path.exists(video_path):
            self.log_utils.log(LogUtils.LOG_LEVEL_ERROR, f"视频文件未找到: {video_path}")
            return None

        try:
            # 计算视频的MD5值
            md5 = MD5Helper.calculate_md5(video_path)
            
            with self.feature_storage as storage:
                # 尝试从数据库获取签名
                signatures = storage.get_signatures(md5)
                
                if not signatures:
                    # 如果数据库中没有，则生成新签名
                    signatures = self._generate_video_signatures(video_path, precision)
                    # 将新签名存入数据库
                    storage.add_features(md5, signatures)
                    self.log_utils.log(LogUtils.LOG_LEVEL_DEBUG, f"新签名已存入数据库。")
                else:
                    self.log_utils.log(LogUtils.LOG_LEVEL_DEBUG, f"从数据库中成功获取 {os.path.basename(video_path)} 的签名。")

            video_name = os.path.basename(video_path)
            alias = None

            # 寻找相似文件的策略：从易到难，依次通过文件名、MD5、视频帧签名来判断
            with self.cache_storage as storage:
                # 1. 从缓存中查找是否已存在同名视频，若存在则复用alias
                existing_video_info_by_name = storage.get_video_info_by_name(video_name)
                if existing_video_info_by_name:
                    alias = existing_video_info_by_name.alias

                # 2. 如果没有同名，则查找是否有相同MD5的视频
                if alias is None:
                    existing_video_info_by_md5 = storage.get_video_info_by_md5(md5)
                    if existing_video_info_by_md5:
                        alias = existing_video_info_by_md5.alias
            
            # 3. 使用图像哈希匹配视频帧签名相似度，若存在相似(超过相似度阈值)则复用alias
            # TODO: 此处需要一个BK-Tree或类似的结构来高效查找具有相似签名的视频
            # TODO: 将签名和md5加入BK-Tree

            # 如果以上步骤都未找到可复用的alias，则使用当前视频的MD5作为新alias
            if alias is None:
                alias = md5

            # 创建VideoInfo对象
            video_info = VideoInfo(path=video_path, video_name=video_name, md5=md5, signatures=signatures, alias=alias)

            # 将新生成的VideoInfo存入缓存
            with self.cache_storage as storage:
                storage.add_video_info(video_info)

            # todo 无需返回video_info
            return video_info

        except subprocess.CalledProcessError as e:
            self.log_utils.log(LogUtils.LOG_LEVEL_ERROR, f"处理视频 {video_path} 的帧失败: {e}")
        except subprocess.TimeoutExpired:
            self.log_utils.log(LogUtils.LOG_LEVEL_ERROR, f"处理视频 {video_path} 的帧超时。")
        except Exception as e:
            self.log_utils.log(LogUtils.LOG_LEVEL_ERROR, f"处理视频 {video_path} 时发生未知错误: {e}")
            
        return None
    
    def find_duplicates(self, video_paths: List[str], precision: int) -> List[List[str]]:
        """
        在给定的视频路径列表中查找重复的视频。

        :param video_paths: 要检查的视频文件路径列表。
        :param precision: 用于计算视频签名的精度（提取的帧数）。
        :return: 一个包含重复视频组的列表，每个组都是一个文件路径列表。
        """
        self.log_utils.log(LogUtils.LOG_LEVEL_INFO, "开始查重任务，首先清空旧缓存...")
        # 在每次查重开始时清空缓存，以确保数据的一致性
        with self.cache_storage as storage:
            storage.clear_cache()
        
        self.log_utils.log(LogUtils.LOG_LEVEL_INFO, f"共找到 {len(video_paths)} 个视频文件。开始计算视频信息...")

        # todo 改为遍历所有路径生成缓存
        for i, path in enumerate(video_paths):
            self.log_utils.log(LogUtils.LOG_LEVEL_INFO, f"正在处理第 {i + 1}/{len(video_paths)} 个视频: {os.path.basename(path)}")
            self._get_video_info(path, precision)

        self.log_utils.log(LogUtils.LOG_LEVEL_INFO, "视频信息计算完成，开始查找重复项...")

        # todo 在VideoInfoCacheStorage表中查找所有具有重复alias的条目，提取并写入表格中


