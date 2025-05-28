import logging

logger = logging.getLogger()


def remove_other_loggers():
  """
  Remove all other loggers except the ones starting with "rag".
  """
  for lib in logging.root.manager.loggerDict:
    if not lib.startswith("campus_rag") and not lib.startswith("src.campus_rag"):
      logging.getLogger(lib).setLevel(logging.WARNING)

remove_other_loggers()



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


remove_other_loggers()
log_level = logging.DEBUG
logger.setLevel(log_level)
console_handler = logging.StreamHandler()
console_handler.setLevel(log_level)
formatter = ColoredFormatter("%(asctime)s - %(levelname)s - %(message)s")
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)