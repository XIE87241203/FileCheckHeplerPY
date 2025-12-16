from typing import List

import utils.sheet_utils as sheet_utils
from get_video_index.file_warehouse import FileWarehouse
from search_video_index.cache_search_helper import CacheSearchHelper
from video_duplicate_check.video_duplicate_checker import VideoDuplicateChecker
import os
from utils.log_utils import LogUtils

# 定义功能索引的常量
REFRESH_CACHE_FUNCTION_INDEX = "1"  # 刷新缓存功能
SEARCH_NAME_FUNCTION_INDEX = "2"  # 搜索名称功能
DEL_FILE_FUNCTION_INDEX = "3"  # 删除文件功能
VIDEO_DUPLICATE_CHECK_FUNCTION_INDEX = "4"  # 视频查重功能
# todo 增加一个选项用于清空VideoInfoCacheStorage

log_utils = LogUtils()


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
            "请输入序号选择功能：\n1.刷新文件库的文件索引。\n2.通过索引查找重复的文件\n3.删除“待删除表”内的文件\n4.视频查重\n输入其他字符结束程序\n"
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
        else:
            # 结束循环
            var = -1
            log_utils.log(LogUtils.LOG_LEVEL_INFO, "结束程序。")


def check_video_duplicates():
    """
    检查视频重复项。
    """
    try:
        precision = int(input("请输入查重精度（建议为5-10的整数）："))
    except ValueError:
        log_utils.log(LogUtils.LOG_LEVEL_ERROR, "精度必须是整数。")
        return

    try:
        checker = VideoDuplicateChecker()
    except FileNotFoundError as e:
        log_utils.log(LogUtils.LOG_LEVEL_ERROR, e)
        return

    log_utils.log(LogUtils.LOG_LEVEL_INFO, "开始获取视频文件列表...")
    cache_map = sheet_utils.get_cache_map()
    video_paths = []
    for path_str in cache_map.values():
        if path_str:
            video_paths.extend(path_str.split('\n'))

    video_paths = list(set(video_paths))  # 去重

    duplicate_groups = checker.find_duplicates(video_paths, precision)

    if not duplicate_groups:
        log_utils.log(LogUtils.LOG_LEVEL_INFO, "未找到重复的视频。")
        return

    log_utils.log(LogUtils.LOG_LEVEL_INFO, f"找到 {len(duplicate_groups)} 组重复的视频。")
    sheet_utils.create_video_duplicate_report_sheet(duplicate_groups)
    log_utils.log(LogUtils.LOG_LEVEL_INFO, f"重复项报告已生成: {sheet_utils.VIDEO_DUPLICATE_REPORT_NAME}")


def del_file():
    # 获取待删除文件列表
    del_path_list = sheet_utils.get_del_path_list()
    # 遍历并删除文件
    for file_path in del_path_list:
        log_utils.log(LogUtils.LOG_LEVEL_INFO, f"删除：{file_path}")
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
    log_utils.log(LogUtils.LOG_LEVEL_INFO, f"读取仓库：{warehouse_path_list}")
    # 初始化文件仓库
    file_warehouse = FileWarehouse(warehouse_path_list)
    # 扫描视频文件
    video_map = file_warehouse.scan_videos()
    log_utils.log(
        LogUtils.LOG_LEVEL_INFO,
        f"读取文件库成功，一共有{len(video_map)}个文件",
    )
    # 创建缓存表格
    sheet_utils.create_cache_table(video_map)


# 程序入口
if __name__ == "__main__":
    main()
