# -*- coding: utf-8 -*-
"""
@author: 日志工具
@time: 2024/05/18
"""
import os
import datetime
import threading
from typing import Any

class LogUtils:
    """
    日志工具类，封装了日志记录的功能（线程安全的单例模式）。
    
    在首次实例化时，会自动在当前运行目录下的 'log' 文件夹中创建以当天日期命名的日志文件。
    """
    _instance = None
    _lock = threading.Lock()

    # --- 日志等级常量 ---
    LOG_LEVEL_ERROR = "ERROR"  # 错误信息
    LOG_LEVEL_INFO = "INFO"    # 重要信息
    LOG_LEVEL_DEBUG = "DEBUG"  # 调试信息

    def __new__(cls, *args, **kwargs):
        """
        实现线程安全的单例模式，确保全局只有一个 LogUtils 实例。
        
        :return: LogUtils 实例
        """
        if not cls._instance:
            with cls._lock:
                # 再次检查，防止多线程环境下重复创建实例
                if not cls._instance:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """
        初始化日志工具。由于是单例，此构造方法仅在第一次实例化时执行一次。
        """
        # 通过检查 _initialized 属性，防止重复初始化
        if hasattr(self, '_initialized'):
            return

        self._log_file_path = None
        try:
            # 获取当前工作目录，并构建日志文件夹路径
            log_dir = os.path.join(os.getcwd(), 'log')
            # 确保日志文件夹存在，如果不存在则创建
            os.makedirs(log_dir, exist_ok=True)
            
            # 使用当前日期命名日志文件
            log_filename = f"{datetime.date.today().strftime('%Y-%m-%d')}.txt"
            self._log_file_path = os.path.join(log_dir, log_filename)
            
            # 记录日志服务的启动
            with open(self._log_file_path, 'a', encoding='utf-8') as f:
                f.write(f"--- Log started at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---\n")
            
            self._initialized = True

        except Exception as e:
            # 如果初始化失败，在控制台打印严重错误
            print(f"[CRITICAL] 无法初始化日志文件: {e}")
            self._log_file_path = None

    def log(self, level: str, message: str, caller: Any = None):
        """
        记录一条日志。

        - INFO 和 ERROR 级别的日志会打印到控制台。
        - 所有级别的日志都会被写入当天的日志文件。
        
        :param level: 日志等级 (例如, LogUtils.LOG_LEVEL_ERROR)。
        :param message: 要记录的日志消息。
        :param caller: 调用者对象或名称 (可选)。
        """
        # 格式化日志消息，包含时间戳和级别
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 获取调用者名称
        caller_name = ""
        if caller:
            if isinstance(caller, str):
                caller_name = f" [{caller}]"
            else:
                caller_name = f" [{caller.__class__.__name__}]"
                
        log_message = f"[{timestamp}] [{level}] {caller_name} {message}"
        
        # 根据日志级别，决定是否在控制台打印
        if level in (self.LOG_LEVEL_INFO, self.LOG_LEVEL_ERROR):
            print(log_message)
        
        # 将日志写入文件（如果日志文件成功初始化）
        if self._log_file_path:
            try:
                with open(self._log_file_path, 'a', encoding='utf-8') as f:
                    f.write(f"{log_message}\n")
            except Exception as e:
                # 如果写入文件失败，则在控制台报告严重错误
                print(f"[CRITICAL] 无法写入日志文件 {self._log_file_path}: {e}")

    def info(self, message: str, caller: Any = None):
        """
        记录 INFO 级别的日志。
        
        :param message: 日志消息内容。
        :param caller: 调用者对象。
        """
        self.log(self.LOG_LEVEL_INFO, message, caller=caller)

    def error(self, message: str, caller: Any = None):
        """
        记录 ERROR 级别的日志。
        
        :param message: 日志消息内容。
        :param caller: 调用者对象。
        """
        self.log(self.LOG_LEVEL_ERROR, message, caller=caller)

    def debug(self, message: str, caller: Any = None):
        """
        记录 DEBUG 级别的日志。
        
        :param message: 日志消息内容。
        :param caller: 调用者对象。
        """
        self.log(self.LOG_LEVEL_DEBUG, message, caller=caller)

# 创建全局实例，方便外部直接导入使用
logger = LogUtils()
