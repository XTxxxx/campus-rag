# Document for developer

# logger的用法
- 不需要被外部调用的模块
  - `import logging`
  - `logger = logging.getLogger(__name__)`即可
- 需要被外部调用的模块
  - 例如带__main__的脚本，typer脚本，pytest脚本
  - `from campus_rag.utils.logging_config import setup_logger`
  - `logger = setup_logger()`

- Develop (with uv)
   - `uv sync --load`
   - Run scripts with uv e.g.     `uv run python -m src.campus_rag.infra.sqlite.init.py`
   - To start backend server, run `uv run uvicorn src.campus_rag.rag.main:app`
   - Before commit, `uv run ruff format .`

- Build
  - `docker build -t whaledge-backend:latest .`

- Deploy
  - `./docker.sh`