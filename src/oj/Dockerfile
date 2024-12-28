FROM python:3.11-slim

# 必要なパッケージのインストール
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# online-judge-toolsのインストール
RUN pip install --no-cache-dir online-judge-tools

# 作業ディレクトリの設定
WORKDIR /workspace

# デフォルトのコマンド
CMD ["oj", "--help"] 