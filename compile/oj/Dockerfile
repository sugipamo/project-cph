FROM python:3.8-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir online-judge-tools

WORKDIR /workspace

ENTRYPOINT ["oj"] 