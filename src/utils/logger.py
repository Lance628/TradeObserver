import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from ..config.settings import LOG_PATH

def setup_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # 确保日志目录存在
    LOG_PATH.mkdir(parents=True, exist_ok=True)
    
    # 文件处理器，指定 encoding='utf-8'
    file_handler = RotatingFileHandler(
        LOG_PATH / f"{name}.log",
        maxBytes=1024 * 1024,  # 1MB
        backupCount=5,
        encoding='utf-8'  # 添加 UTF-8 编码设置
    )
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    
    # 格式化
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'  # 可选：自定义时间格式
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # 避免重复日志
    if logger.hasHandlers():
        logger.handlers.clear()
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger
