import re
from typing import List, Dict, Tuple
from src.utils.log_utils import logger


class CacheSearchHelper:
    """
    在缓存的map中搜索文件。
    这个类通过接收一个文件名到路径的映射（缓存），
    然后根据提供的搜索列表和忽略规则，来查找匹配的文件。
    """

    def __init__(self, cache_map: Dict[str, str], search_content_list: List[str], ignore_texts: List[str]):
        """
        构造函数，用于初始化搜索器。

        :param cache_map: 文件名到文件路径的映射字典。key为文件名，value为路径。
        :param search_content_list: 需要搜索的文件名（或部分文件名）列表。
        :param ignore_texts: 在构建搜索模式时需要忽略（即用.*通配符替代）的文字列表。
        """
        self.cache_map = cache_map  # 文件缓存，{文件名: 文件路径}
        self.search_content_list = search_content_list  # 需要搜索的内容列表
        self.ignore_texts = ignore_texts  # 搜索时需要忽略的特殊文本

    def start_search(self) -> Tuple[Dict[str, str], List[str]]:
        """
        开始执行搜索。

        该方法会遍历搜索列表，为每一项生成一个正则表达式，
        然后在缓存的map中查找匹配的文件名。

        :return: 一个元组，包含两个元素:
                 - match_map: 一个字典，key为原始搜索内容，value为所有匹配的文件路径（如果存在多个匹配，则用换行符'\n'分隔）。
                 - mismatch_list: 一个列表，包含所有没有在缓存中找到任何匹配的搜索内容。
        """
        match_map = {}  # 用于存放搜索成功的结果，{搜索内容: 匹配的路径}
        mismatch_list = []  # 用于存放未匹配到的搜索内容

        # 遍历每一个要搜索的内容
        for content in self.search_content_list:
            pattern_str = content
            # 将搜索内容中的特定文本替换为正则表达式的通配符 '.*'
            # 这样做可以忽略掉不重要的部分，实现更灵活的模糊匹配
            for ignore_text in self.ignore_texts:
                pattern_str = pattern_str.replace(ignore_text, ".*")

            try:
                # 预编译正则表达式以提高执行效率。
                # f".*{pattern_str}.*" 表示模式可以在文件名中的任何位置出现。
                regex = re.compile(f".*{pattern_str}.*")
            except re.error as e:
                # 如果创建正则表达式失败（例如，模式包含无效的语法），则记录错误并跳过。
                logger.error(f"为'{content}'创建正则表达式失败: {e}")
                mismatch_list.append(content)
                continue  # 继续处理下一个搜索内容

            found_paths = []  # 存储当前搜索内容所有匹配到的文件路径
            # 遍历缓存中的每一个文件
            for file_name, path in self.cache_map.items():
                # 使用正则表达式的search方法在文件名中查找匹配项
                if regex.search(file_name):
                    found_paths.append(path)  # 如果找到匹配项，则将其路径添加到列表中

            # 判断是否找到了匹配的路径
            if found_paths:
                # 如果找到了，将原始搜索内容和所有匹配的路径（用换行符连接）存入成功字典
                match_map[content] = "\n".join(found_paths)
            else:
                # 如果没有找到任何匹配项，则将原始搜索内容存入未匹配列表
                mismatch_list.append(content)

        # 返回包含匹配结果和未匹配列表的元组
        return match_map, mismatch_list
