# Campus RAG（迭代二）

> 校园信息RAG应用

- 我们的侧重点
  - [x] 老师的相关信息
  - [x] 课表
  - [ ] 红黑榜
  - [ ] 学生手册

-  Develop
   - Activate a venv `python3.10 venv .venv ; source .venv/bin/activate`
   - `pip install -e .`
   - Run scripts in root directory e.g. `python src/campus_rag/chunk/milvus_init.py`
   - To start backend server, run `fastapi run src/campus_rag/api/main.py`

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