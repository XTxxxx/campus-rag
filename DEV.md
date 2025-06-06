# Document for developer

# logger的用法
- 不需要被外部调用的模块
  - `import logging`
  - `logger = logging.getLogger(__name__)`即可
- 需要被外部调用的模块
  - 例如带__main__的脚本，typer脚本，pytest脚本
  - `from campus_rag.utils.logging_config import setup_logger`
  - `logger = setup_logger()`