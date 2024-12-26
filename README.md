# AtCoder CLI Tool (Rust)

## 概要

AtCoderのコンテスト問題の管理、テスト実行、提出を効率化するCLIツールです。
Rustを標準言語として実装されています。

## 基本機能

### 通常問題への対応
online-judge-toolsを利用した以下の機能を提供:
```
ojt <contest_id> <command> <problem_id> [options]
```

- `o`: 問題ファイルの作成とテストケースの取得
- `t`: テストケース実行（並列実行、タイムアウト5秒）
  - サンプルケースの実行
  - カスタムケースの実行（`x_gen.rs`が存在する場合）
- `s`: AtCoderへの提出

### AHC特有の機能
```
ojt <contest_id> ahctest <number_of_cases>
```
- ツール類の自動セットアップ（本体、webvisualizer）
- テストケース生成と実行（seed値、in/out/other）
- Git/Cargoによるコード・ビジュアライザー管理

## プロジェクト構成
```
ojt/
├── src/      # ツール本体
├── tests/    # テストコード
├── contest/  # 問題ファイル
│   ├── template/
│   │   ├── main.rs    # Rustテンプレート
│   │   └── gen.rs     # テストケース生成テンプレート
│   └── abc300/  # コンテストディレクトリ例
│       ├── a.rs
│       └── test/
│           ├── sample-1.in   # サンプルケース
│           ├── sample-1.out
│           ├── custom-1.in   # 生成したテストケース
│           └── custom-1.out
├── .temp/    # 一時ファイル
├── Cargo.toml    # Rust依存関係
├── compose.yml   # Docker設定
└── ojt          # バイナリ
```

## 実行環境

### Docker環境
- CPU: 2コア
- メモリ: 1024MB
- Rust (5054): rust:1.70
- 外部ツール: online-judge-tools, Cargo, Git

## 開発環境
- Rust 1.70以上
  - cargo-watch: 開発用ホットリロード
  - clippy: リンター
  - rustfmt: コードフォーマッタ
- Docker
  - マルチステージビルド
  - 軽量イメージの使用
- Git
  - バージョン管理
  - ブランチ戦略
  - CI/CD連携

## インストール方法

1. Dockerのインストール
2. リポジトリのクローン
3. 以下のコマンドで環境構築:
```bash
docker compose up -d
```

## 使用方法

1. コンテストへの参加:
```bash
ojt abc300 o a
```

2. テストの実行:
```bash
ojt abc300 t a
```

3. 解答の提出:
```bash
ojt abc300 s a
```

4. AHCのテスト実行:
```bash
ojt ahc001 ahctest 100
``` 