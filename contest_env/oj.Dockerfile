FROM python:3.10

RUN pip install --upgrade pip
RUN pip install online-judge-tools

RUN mkdir -p /workspace
WORKDIR /workspace