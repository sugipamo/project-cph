FROM ubuntu:22.04

# 基本パッケージのインストール
RUN apt-get update && apt-get install -y \
    g++ \
    gdb \
    valgrind \
    clang \
    clang-format \
    cmake \
    make \
    curl \
    wget \
    git \
    python3 \
    python3-pip \
    vim \
    && rm -rf /var/lib/apt/lists/*

# 最新のC++コンパイラーサポート
RUN apt-get update && apt-get install -y \
    gcc-11 \
    g++-11 \
    && update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-11 100 \
    && update-alternatives --install /usr/bin/g++ g++ /usr/bin/g++-11 100

# 競技プログラミング用ツール
RUN pip3 install online-judge-tools

# 作業ディレクトリの設定
WORKDIR /workspace

# デフォルトコマンド
CMD ["bash"]