FROM rust:1.70

# PyPyのインストール
RUN apt-get update && apt-get install -y \
    pypy3 \
    && rm -rf /var/lib/apt/lists/*

# ワークスペースの設定
WORKDIR /app
COPY . .
RUN cargo install --path .

# テスト実行用のディレクトリ
WORKDIR /workspace 