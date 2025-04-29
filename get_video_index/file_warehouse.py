import os


class FileWarehouse:

    def __init__(self, dir_path_list):  # 构造函数
        self.dir_path_list = dir_path_list  # 将参数绑定到实例属性

    video_formats = [
        ".mp4",
        ".avi",
        ".mkv",
        ".mov",
        ".wmv",
        ".flv",
        ".webm",
        ".mpeg",
        ".mpg",
        ".3gp",
        ".m4v",
        ".ogg",
        ".vob",
        ".ts",
        ".rmvb",
        ".m2ts",
    ]

    # 初始化目录列表
    def scan_video(self):
        for i in range(len(self.dir_path_list)):
            dir = self.dir_path_list[i]
            print(f'读取"{dir}"中，{i+1}/{len(self.dir_path_list)}')
            self.find_videos(dir)
        return self.video_map

    # dir_list = []
    # # 内容是名字与路径列表
    video_map = {}

    def is_video_file(self, file_name):
        return any(file_name.lower().endswith(fmt) for fmt in self.video_formats)

    def find_videos(self, root_dir):
        # 遍历所有子目录的视频文件
        for root, _, files in os.walk(root_dir):
            for file in files:
                if self.is_video_file(file):
                    _abs_path = os.path.abspath(os.path.join(root, file))
                    if file in self.video_map:
                        # 已经有同名文件
                        self.video_map[file].append(_abs_path)
                    else:
                        self.video_map[file] = [_abs_path]
