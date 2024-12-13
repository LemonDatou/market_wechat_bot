import os
import logging
from logging.handlers import TimedRotatingFileHandler
import datetime
import sys

class CustomTimedRotatingFileHandler(TimedRotatingFileHandler):
    def __init__(self, log_dir, **kwargs):
        # 初始化父类，设置一个临时文件名
        self.log_dir = log_dir
        temp_log_file = os.path.join(log_dir,f"{datetime.datetime.now().strftime('%Y-%m-%d')}.log")
        super().__init__(temp_log_file, **kwargs)

    def _get_new_log_file_name(self):
        # 生成新的日志文件名
        current_date = datetime.datetime.now().strftime("%Y-%m-%d")
        return os.path.join(self.log_dir, f"{current_date}.log")

    def doRollover(self):
        # 重写日志切换逻辑，确保日志文件按日期命名
        self.stream.close()
        self.baseFilename = self._get_new_log_file_name()
        if not self.delay:
            self.stream = self._open()

script_name = os.path.basename(sys.argv[0])
script_name = script_name[:-3]
# 获取调用脚本所在目录
# caller_dir = os.path.abspath(os.getcwd())  # 获取调用脚本的当前工作目录
logging_dir = os.path.dirname(os.path.abspath(__file__))
caller_dir = os.path.dirname(logging_dir)

# 创建 logs 文件夹路径
log_dir = os.path.join(caller_dir, "logs")
os.makedirs(log_dir, exist_ok=True)  # 如果不存在则创建

log_dir = os.path.join(log_dir, script_name)
os.makedirs(log_dir, exist_ok=True)  # 如果不存在则创建

# 日志文件以日期命名
log_file = os.path.join(log_dir, f"{datetime.datetime.now().strftime('%Y-%m-%d')}.log")

# 创建日志记录器
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# 设置日志格式
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

# 创建文件处理器，并设置为按天轮转
file_handler = CustomTimedRotatingFileHandler(
    log_dir=log_dir,
    when="midnight",
    interval=1,
    backupCount=7,
    encoding='utf-8'
)
# file_handler.suffix = "%Y-%m-%d.log"
file_handler.setFormatter(formatter)

# 添加处理器到日志记录器
logger.addHandler(file_handler)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

def handle_uncaught_exceptions(exc_type, exc_value, exc_traceback):
    """捕获未处理的异常并写入日志"""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)  # 不拦截 Ctrl+C 中断
        return
    logger.critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

# 设置全局异常处理
sys.excepthook = handle_uncaught_exceptions

def log_info(*args):
    """支持多个参数的 info 日志"""
    message = " ".join(map(str, args))  # 将多个参数拼接为字符串
    logger.info(message)

def log_error(*args):
    """支持多个参数的 error 日志"""
    message = " ".join(map(str, args))
    logger.error(message)