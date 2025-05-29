import logging
import sys


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
  name="campus_rag", level=logging.DEBUG, need_config: bool = True
) -> logging.Logger:
  if not need_config:
    return logging.getLogger(name)
  logger = logging.getLogger(name)
  logger.setLevel(level)
  logger.propagate = False  # 防止冒泡到 root logger

  # if not logger.handlers:
  formatter = ColoredFormatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
  console_handler = logging.StreamHandler(sys.stdout)
  console_handler.setFormatter(formatter)
  logger.addHandler(console_handler)
  return logger
