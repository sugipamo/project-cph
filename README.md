# cph (Competitive Programming Helper)

競技プログラミングの問題を解くためのCLIツールです。

## 主な機能

- 🔑 AtCoderへの簡単なログイン
- 🚀 問題の自動セットアップ
- 📝 テンプレートの自動生成
- 🌐 エディタとブラウザでの問題ページの自動オープン
- ✅ 基本的なテスト実行（メモリ制限、タイムアウト処理付き）
- 🔍 エラーメッセージの構造化表示
- 📤 解答の提出（テスト実行付き）

## クイックスタート

### 1. 必要な環境

- Rust toolchain
- Docker
- VSCode または Cursor

### 2. インストール

```bash
cargo install --path .
```

### 3. 基本的な使い方

```bash
# ログイン
cph atcoder login

# コンテストの設定
cph atcoder work abc001

# 問題を開く
cph atcoder open a

# テストを実行
cph atcoder test a

# 解答を提出
cph atcoder submit a
```

## 詳細なドキュメント

より詳細な情報は以下のドキュメントを参照してください：

- [インストールガイド](docs/installation.md)
  - 環境構築の詳細な手順
  - トラブルシューティング
- [使用方法](docs/usage.md)
  - コマンドの詳細な説明
  - 各機能の使用例
- [設定ガイド](docs/configuration.md)
  - 設定ファイルの説明
  - テンプレートのカスタマイズ
- [開発者向け情報](docs/development.md)
  - プロジェクト構造
  - テスト方法
  - コントリビューション方法

## サポート言語

現在、以下の言語をサポートしています：
- Rust
- PyPy

## ライセンス

このプロジェクトは [MIT License](LICENSE) の下で公開されています。 