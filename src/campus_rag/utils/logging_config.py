import logging


def configure_logger(level: str = "INFO"):
  """
  Configure the logger for the application.
  :param level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
  """
  level_dict = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "critical": logging.CRITICAL,
  }

  log_level = level_dict.get(level.lower(), logging.INFO)

  logging.basicConfig(
    level=log_level,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%H:%M:%S",
  )

  # if not logger.handlers:
  # logger.setLevel(log_level)

  # console_handler = logging.StreamHandler()
  # console_handler.setLevel(log_level)
  # formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%H:%M:%S')
  # console_handler.setFormatter(formatter)

  # logger.addHandler(console_handler)

  # file_handler = logging.FileHandler("app.log")
  # file_handler.setFormatter(formatter)
  # logger.addHandler(file_handler)
