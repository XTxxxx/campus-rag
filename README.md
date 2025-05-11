# Whaledge Copilot（迭代二）
![欢迎界面截图](./assets/welcome.png)
## 项目概览

- 集成的数据
  - [x] 老师的相关信息
  - [x] 红黑榜
  - [ ] 课表
  - [ ] 学生手册
  - [ ] 迭代三再做吧...


- **优点（项目组织方面）**
  - 使用 uv 进行项目管理 
  - 使用 docker 部署rag项目
  - 使用 docker compose 部署milvus向量数据库
  - 使用jenkins进行cicd
  - 总之就是尽可能是环境配置简单了


- **优点（功能方面）**
  - 全面支持sse，rag pipeline实时推流
  - rag pipeline易于裁切，调参优化

- 待改进的地方
  - 支持多用户对话，持久化对话数据
  - 丰富数据源，进一步清洗数据；优化检索策略；在线检索


## 开发者

- Develop (with uv)
   - `uv sync --load`
   - Run scripts with uv e.g.     `uv run python src/campus_rag/chunk/milvus_init.py`
   - To start backend server, run `uv run uvicorn src.campus_rag.rag.api.main:app`
   - Before commit, `uv run ruff format .`

- Build
  - `docker build -t whaledge-backend:latest .`

- Deploy
  ``` sh
  docker run --name whaledge-backend -d  \
  -v /home/xtx/.cache/huggingface:/root/.cache/huggingface   \
  --network=host  \
  -e QWEN_API_KEY=$QWEN_API_KEY  \
  -e HTTP_PROXY = 'desensitized'
  -e HTTPS_PROXY = 'desensitized'
  --gpus all  \
  --restart unless-stopped \
  whaledge-backend:latest
  ```