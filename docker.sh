#!/bin/bash

docker rm -f whaledge-backend-container

docker run --name whaledge-backend-container -d \
                            -v /home/xtx/.cache/huggingface:/root/.cache/huggingface \
                            --network=host \
                            -e LCX_QWEN_API_KEY=${LCX_QWEN_API_KEY} \
                            -e HTTP_PROXY = 'desensitized'
                            -e HTTPS_PROXY = 'desensitized'
                            --gpus all \
                            --restart unless-stopped \
                            whaledge-backend:latest