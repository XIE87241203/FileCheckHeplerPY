import re


class CacheSearchHepler:
    def __init__(self, cache_map, search_content_list, ignore_texts):  # 构造函数
        self.cache_map = cache_map
        self.search_content_list = search_content_list
        self.ignore_texts = ignore_texts

    def start_search(self):
        search_rex_list = []
        for content in self.search_content_list:
            replaceName = content
            for ignore_text in self.ignore_texts:
                replaceName = replaceName.replace(ignore_text, ".*")
            search_rex_list.append(f".*{replaceName}.*")
        # key为文件名，value为路径
        match_map = {}
        mismatch_list = []
        # 将cache_map转化为json
        all_file_name_str = "\n".join(self.cache_map.keys())  # 直接拼接键

        # 开始使用正则搜索
        for i in range(len(search_rex_list)):
            # //找出匹配的文件名
            matches = re.findall(search_rex_list[i], all_file_name_str)
            
            if len(matches) > 0:  # 检查列表是否非空
                path = ""
                for match_name in matches:
                    path += f"{self.cache_map[match_name]}\n"
                match_map[self.search_content_list[i]] = path
            else:
                mismatch_list.append(self.search_content_list[i])

        return match_map, mismatch_list
