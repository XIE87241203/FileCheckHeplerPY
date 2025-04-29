import utils.sheet_utils as sheet_utils
from get_video_index.file_warehouse import FileWarehouse
from search_video_index.cache_search_helper import CacheSearchHepler
import os

REFRESH_CACHE_FUNCTION_INDEX = "1"
SEARCH_NAME_FUNCTION_INDEX = "2"
DEL_FILE_FUNCTION_INDEX = "3"

# 使用pyinstaller --onefile --name=MyApp main.py 打包成exe
# todo 缓存数据查重，批量删除功能


def main():
    ignore_texts = ["-", "_"]
    # 这是主函数
    # 检查并创建配置文件
    sheet_utils.check_and_create_config_sheet()
    var = 1
    while var == 1:  # 死循环
        function_num = input(
            "请输入序号选择功能：\n1.刷新文件库的文件索引。\n2.通过索引查找重复的文件\n3.删除“待删除表”内的文件\n输入其他字符结束程序\n"
        )  # 提示用户输入
        if function_num == REFRESH_CACHE_FUNCTION_INDEX:
            refresh_file_name_cache()
        elif function_num == SEARCH_NAME_FUNCTION_INDEX:
            cache_map = sheet_utils.get_cache_map()
            search_content_list = sheet_utils.get_search_content_list()
            search_helper = CacheSearchHepler(
                cache_map, search_content_list, ignore_texts
            )
            match_map, mismatch_list = search_helper.start_search()
            sheet_utils.create_result_sheet(match_map, mismatch_list)
        elif function_num == DEL_FILE_FUNCTION_INDEX:
            del_path_list = sheet_utils.get_del_path_list()
            for file_path in del_path_list:
                print(f"删除：{file_path}")
                os.remove(file_path)
        else:
            var = -1
            print("结束程序。")


def refresh_file_name_cache():
    warehouse_path_list = sheet_utils.get_warehouse_path_list()
    print("读取仓库：", warehouse_path_list)
    file_warehouse = FileWarehouse(warehouse_path_list)
    videoMap = file_warehouse.scan_video()
    print(
        f"读取文件库成功，一共有{len(videoMap)}个文件",
    )
    sheet_utils.create_cache_table(videoMap)


if __name__ == "__main__":
    main()  # 程序入口
1
