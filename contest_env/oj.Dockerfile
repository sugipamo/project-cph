FROM docker.io/library/python:3.9

RUN pip install --upgrade pip
RUN pip install online-judge-tools

RUN mkdir -p /workspace
WORKDIR /workspace