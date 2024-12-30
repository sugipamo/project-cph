# インストールガイド

## 必要な環境

### 1. Rust toolchain

```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

インストール後、以下のコマンドで正しくインストールされたか確認できます：
```bash
rustc --version
cargo --version
```

### 2. Docker

#### Windows/macOS
- [Docker Desktop](https://www.docker.com/products/docker-desktop/)をインストール

#### Linux
```bash
curl -fsSL https://get.docker.com | sh
```

インストール後の確認：
```bash
docker --version
docker run hello-world
```

### 3. 言語環境

#### Rust
上記のRust toolchainで対応

#### PyPy
Dockerコンテナで実行されるため、ローカルへのインストールは不要

### 4. エディタ
以下のいずれかをインストール：
- [Visual Studio Code](https://code.visualstudio.com/)
  - 推奨拡張機能：
    - rust-analyzer
    - Python
    - YAML
- [Cursor](https://cursor.sh/)

## cphのインストール

1. リポジトリをクローン：
```bash
git clone [リポジトリURL]
cd cph
```

2. インストール：
```bash
cargo install --path .
```

3. インストールの確認：
```bash
cph --version
```

## トラブルシューティング

### よくある問題

1. Rustのインストールエラー
   - 原因: システムの依存関係が不足している
   - 解決: `build-essential`パッケージをインストール
     ```bash
     sudo apt-get update
     sudo apt-get install build-essential
     ```

2. Dockerの起動エラー
   - 原因: Dockerデーモンが起動していない
   - 解決:
     ```bash
     sudo systemctl start docker
     sudo systemctl enable docker
     ```

3. 権限エラー
   - 原因: Dockerグループに所属していない
   - 解決:
     ```bash
     sudo usermod -aG docker $USER
     # ログアウトして再ログイン
     ```

### エラーの報告方法

問題が解決しない場合は、以下の情報を含めてイシューを作成してください：
1. OSのバージョン
2. 各コンポーネントのバージョン情報
3. エラーメッセージの全文
4. 実行したコマンドと手順 