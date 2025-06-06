import logging
import os
import sys
from campus_rag.constants.log import LOG_FILE_PATH


class ColoredFormatter(logging.Formatter):
  """
  Custom formatter to add colors to log messages.
  """

  COLORS = {
    "DEBUG": "\033[94m",  # Blue
    "INFO": "\033[92m",  # Green
    "WARNING": "\033[93m",  # Yellow
    "ERROR": "\033[91m",  # Red
    "CRITICAL": "\033[95m",  # Magenta
  }
  RESET = "\033[0m"  # Reset color

  def format(self, record):
    log_color = self.COLORS.get(record.levelname, self.RESET)  # Default color
    message = super().format(record)
    return f"{log_color}{message}{self.RESET}"  # Reset color at the end


def setup_logger(
  name="campus_rag", level=logging.DEBUG, need_config: bool = True, log2file=False
) -> logging.Logger:
  logger = logging.getLogger(name)
  if not need_config:
    return logger
  logger.setLevel(level)
  logger.propagate = False  # 防止冒泡到 root logger

  # if not logger.handlers:
  formatter = ColoredFormatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
  console_handler = logging.StreamHandler(sys.stdout)
  console_handler.setFormatter(formatter)
  logger.addHandler(console_handler)
  if log2file:
    os.unlink(LOG_FILE_PATH) if os.path.exists(
      LOG_FILE_PATH
    ) else None  # 清理旧日志文件
    os.makedirs(os.path.dirname(LOG_FILE_PATH), exist_ok=True)
    file_handler = logging.FileHandler(LOG_FILE_PATH, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

  if "uvicorn" in sys.modules:
    for uvicorn_logger_name in ["uvicorn", "uvicorn.access", "uvicorn.error"]:
      uvicorn_logger = logging.getLogger(uvicorn_logger_name)
      if log2file:
        uvicorn_logger.addHandler(file_handler)

  return logger
