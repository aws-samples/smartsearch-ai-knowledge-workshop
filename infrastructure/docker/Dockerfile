FROM nvidia/cuda:12.2.0-devel-ubuntu22.04 AS base

## install python and pip
RUN apt-get update -y
RUN apt-get install --assume-yes software-properties-common
RUN apt-get install python3-pip -y
RUN apt-get install vim -y

## create user instead root
RUN adduser --disabled-login --gecos "First Last,RoomNumber,WorkPhone,HomePhone" llm
USER llm
WORKDIR /home/llm
ENV PATH="/home/llm/.local/bin:${PATH}"

# update pip
RUN pip3 install --upgrade pip
# COPY chatglm2-6b chatglm-6b and MAKE the following files cachable
COPY chatglm2-6b/config.json chatglm-6b/config.json
COPY chatglm2-6b/configuration_chatglm.py chatglm-6b/configuration_chatglm.py
COPY chatglm2-6b/modeling_chatglm.py chatglm-6b/modeling_chatglm.py
COPY chatglm2-6b/MODEL_LICENSE chatglm-6b/MODEL_LICENSE
COPY chatglm2-6b/pytorch_model-00001-of-00007.bin chatglm-6b/pytorch_model-00001-of-00007.bin
COPY chatglm2-6b/pytorch_model-00002-of-00007.bin chatglm-6b/pytorch_model-00002-of-00007.bin
COPY chatglm2-6b/pytorch_model-00003-of-00007.bin chatglm-6b/pytorch_model-00003-of-00007.bin
COPY chatglm2-6b/pytorch_model-00004-of-00007.bin chatglm-6b/pytorch_model-00004-of-00007.bin
COPY chatglm2-6b/pytorch_model-00005-of-00007.bin chatglm-6b/pytorch_model-00005-of-00007.bin
COPY chatglm2-6b/pytorch_model-00006-of-00007.bin chatglm-6b/pytorch_model-00006-of-00007.bin
COPY chatglm2-6b/pytorch_model-00007-of-00007.bin chatglm-6b/pytorch_model-00007-of-00007.bin
COPY chatglm2-6b/pytorch_model.bin.index.json chatglm-6b/pytorch_model.bin.index.json
COPY chatglm2-6b/quantization.py chatglm-6b/quantization.py
COPY chatglm2-6b/README.md chatglm-6b/README.md
COPY chatglm2-6b/tokenization_chatglm.py chatglm-6b/tokenization_chatglm.py
COPY chatglm2-6b/tokenizer_config.json chatglm-6b/tokenizer_config.json
COPY chatglm2-6b/tokenizer.model chatglm-6b/tokenizer.model


FROM base AS llm_smart_search_python_env
## copy requirements and install dependencies
COPY --chown=llm:llm requirements.txt .
RUN pip3 install --ignore-installed --no-cache-dir --user -r requirements.txt

FROM llm_smart_search_python_env AS llm_smart_search
COPY --chown=llm:llm main.py .

## run the application
CMD [ "flask", "--app", "main", "run","--host","0.0.0.0","--port","5000"]