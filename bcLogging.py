import logging
import os
import time

# 创建日志格式
mono_formatter = logging.Formatter('[%(asctime)s][%(levelname)s]<%(name)s> %(message)s')

# 创建根日志记录器
logging.root.setLevel(logging.DEBUG)

# 文件日志处理器
os.makedirs('bcLog', exist_ok=True)
file_handler = logging.FileHandler(time.strftime('bcLog/Log_%Y-%m-%d_%H.%M.%S.txt'))
file_handler.setFormatter(mono_formatter)
file_handler.setLevel(logging.DEBUG)
logging.root.addHandler(file_handler)

# 控制台日志处理器
console_handler = logging.StreamHandler()
console_handler.setFormatter(mono_formatter)
console_handler.setLevel(logging.INFO)
logging.root.addHandler(console_handler)

def getLogger(name):
    return logging.getLogger('bc.' + name)

logger = getLogger('main')

logger.info('Battle Cats Script Initialized')
