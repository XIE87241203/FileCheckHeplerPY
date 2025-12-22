from typing import List

import utils.sheet_utils as sheet_utils
from get_video_index.file_warehouse import FileWarehouse
from search_video_index.cache_search_helper import CacheSearchHelper
import os

from src.video_duplicate_check.utils.video_cache_manager import VideoCacheManager
from src.video_duplicate_check.video_duplicate_checker import VideoDuplicateChecker
from utils.log_utils import logger

# 定义功能索引的常量
REFRESH_CACHE_FUNCTION_INDEX = "1"  # 刷新缓存功能
SEARCH_NAME_FUNCTION_INDEX = "2"  # 搜索名称功能
DEL_FILE_FUNCTION_INDEX = "3"  # 删除文件功能
VIDEO_DUPLICATE_CHECK_FUNCTION_INDEX = "4"  # 视频查重功能
CLEAR_VIDEO_DUPLICATE_CACHE_FUNCTION_INDEX = "5"  # 清空视频查重缓存功能

# 使用pyinstaller --onefile --name=MyApp main.py 打包成exe


def main():
    """
    主函数，程序的入口点。
    """
    # 定义在搜索时需要忽略的字符
    ignore_texts = ["-", "_"]
    # 检查并创建配置文件
    sheet_utils.check_and_create_config_sheet()
    # 循环标志
    var = 1
    # 开始主循环，让用户选择功能
    while var == 1:
        function_num = input(
            "请输入序号选择功能：\n1.刷新文件库的文件索引。\n2.通过索引查找重复的文件\n3.删除“待删除表”内的文件\n4.视频查重\n5.清空视频查重缓存\n输入其他字符结束程序\n"
        )  # 提示用户输入
        # 根据用户的输入选择不同的功能
        if function_num == REFRESH_CACHE_FUNCTION_INDEX:
            # 刷新文件名缓存
            refresh_file_name_cache()
        elif function_num == SEARCH_NAME_FUNCTION_INDEX:
            search_name(ignore_texts)
        elif function_num == DEL_FILE_FUNCTION_INDEX:
            del_file()
        elif function_num == VIDEO_DUPLICATE_CHECK_FUNCTION_INDEX:
            check_video_duplicates()
        elif function_num == CLEAR_VIDEO_DUPLICATE_CACHE_FUNCTION_INDEX:
            clear_video_duplicates_cache()
        else:
            # 结束循环
            var = -1
            logger.info("结束程序。")


def clear_video_duplicates_cache():
    """
    清空视频查重相关的缓存数据库。
    """
    confirm = input("确定要清空所有视频查重缓存吗？(y/n): ").strip().lower()
    if confirm == 'y':
        cache_manager = VideoCacheManager()
        cache_manager.clear_all_cache()
        logger.info("视频查重缓存已清空。")
    else:
        logger.info("取消清空缓存操作。")


def check_video_duplicates():
    """
    检查视频重复项。
    """
    path = input("请输入要查重的文件夹路径: ").strip()
    if not os.path.exists(path):
        logger.error(f"路径不存在: {path}")
        return
    if not os.path.isdir(path):
        logger.error(f"输入的不是文件夹路径: {path}")
        return

    video_duplicate_checker = VideoDuplicateChecker(path)
    video_duplicate_checker.start()


def del_file():
    # 获取待删除文件列表
    del_path_list = sheet_utils.get_del_path_list()
    # 遍历并删除文件
    for file_path in del_path_list:
        logger.info(f"删除：{file_path}")
        os.remove(file_path)


def search_name(ignore_texts: List[str]):
    # 从表格中获取缓存数据
    cache_map = sheet_utils.get_cache_map()
    # 从表格中获取要搜索的内容
    search_content_list = sheet_utils.get_search_content_list()
    # 初始化搜索帮助类
    search_helper = CacheSearchHelper(
        cache_map, search_content_list, ignore_texts
    )
    # 开始搜索
    match_map, mismatch_list = search_helper.start_search()
    # 获取链接前缀
    link_prefix = sheet_utils.get_link_prefix()
    # 创建结果表格
    sheet_utils.create_result_sheet(match_map, mismatch_list, link_prefix)


def refresh_file_name_cache():
    """
    刷新文件名缓存。
    会扫描指定仓库路径下的所有视频文件，并将其信息创建成一个缓存表格。
    """
    # 从表格中获取仓库路径
    warehouse_path_list = sheet_utils.get_warehouse_path_list()
    logger.info(f"读取仓库：{warehouse_path_list}")
    # 初始化文件仓库
    file_warehouse = FileWarehouse(warehouse_path_list)
    # 扫描视频文件
    video_map = file_warehouse.scan_videos()
    logger.info(
        f"读取文件库成功，一共有{len(video_map)}个文件",
    )
    # 创建缓存表格
    sheet_utils.create_cache_table(video_map)


# 程序入口
if __name__ == "__main__":
    main()
