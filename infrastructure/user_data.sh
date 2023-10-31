#!/bin/sh

REGION=$(curl -s http://169.254.169.254/latest/dynamic/instance-identity/document | jq -r .region)
account=$(curl -s http://169.254.169.254/latest/dynamic/instance-identity/document | jq -r .accountId)

## login
docker login --username AWS --password $(aws ecr get-login-password --region ${REGION})
aws ecr get-login-password --region ${REGION} | docker login --username AWS --password-stdin ${account}.dkr.ecr.${REGION}.amazonaws.com

## pull image
docker pull --verbose ${account}.dkr.ecr.${REGION}.amazonaws.com.cn/llm_smart_search:latest

## run the image
docker run --gpus '"device=0"' -p 5000:5000 -it -d --restart=on-failure ${account}.dkr.ecr.${REGION}.amazonaws.com.cn/llm_smart_search:latest
