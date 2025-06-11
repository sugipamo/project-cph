FROM gcc:11

RUN mkdir -p /workspace
WORKDIR /workspace

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install online-judge-tools