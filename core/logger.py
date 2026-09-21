import os
import sys
import datetime
import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path


def init_logger(data_dir: str = "data/logs", log_filename: str = "emby-ranks.log", level: int = logging.INFO):
    """
    初始化系统全局日志配置 (双通道输出: 控制台 + 按天自动归档持久化文件)
    
    :param data_dir: 日志存放目录 (默认 data/logs，自动持久化至挂载卷)
    :param log_filename: 当前活动日志文件名
    :param level: 日志输出级别
    """
    log_path = Path(data_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    
    file_path = log_path / log_filename
    log_format = "%(asctime)s [%(levelname)s] %(name)s - %(message)s"
    formatter = logging.Formatter(log_format)

    # 1. 控制台输出 Handler (供 docker logs 实时查看)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(level)

    # 2. 按天滚动文件 Handler (每天 00:00:00 自动切分，最多保留 7 天历史文件，UTF-8 编码)
    file_handler = TimedRotatingFileHandler(
        filename=str(file_path),
        when="midnight",
        interval=1,
        backupCount=7,
        encoding="utf-8",
        atTime=datetime.time(0, 0, 0)
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(level)

    # 3. 配置 Root Logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # 清除旧的 handlers 避免重复添加
    if root_logger.handlers:
        root_logger.handlers.clear()
        
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    # 4. 降低高频第三方网络请求库的日志噪音
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

    return root_logger
