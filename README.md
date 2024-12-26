# AtCoder CLI Tool (Rust)

## 概要

AtCoderのコンテスト問題の管理、テスト実行、提出を効率化するCLIツールです。
Rustを標準言語として実装されています。

## 基本機能

### 通常問題への対応
online-judge-toolsを利用した以下の機能を提供:
```
cph <contest_id> <command> <problem_id> [options]
```

- `o`: 問題ファイルの作成とテストケースの取得
- `t`: テストケース実行（並列実行、タイムアウト5秒）
  - サンプルケースの実行
  - カスタムケースの実行（`x_gen.rs`が存在する場合）
- `s`: AtCoderへの提出

### AHC特有の機能 (TODO)
```
cph <contest_id> ahctest <number_of_cases>
```
- ツール類の自動セットアップ（本体、webvisualizer）
- テストケース生成と実行（seed値、in/out/other）
- Git/Cargoによるコード・ビジュアライザー管理

## プロジェクト構成
```
cph/
├── src/           # ソースコード
│   ├── bin/       # 実行可能ファイル
│   │   └── cph.rs # メインバイナリ
│   └── lib.rs     # ライブラリコード
├── examples/      # サンプルコード
├── benches/       # ベンチマークテスト
├── tests/         # 統合テスト
├── workspace/     # 現在取り組んでいる問題
│   ├── abc/      # AtCoder Beginner Contest
│   │   ├── contest.yaml  # 現在のコンテスト情報
│   │   ├── template/    # 言語別テンプレート
│   │   │   ├── main.rs  # Rust用
│   │   │   ├── gen.rs
│   │   │   ├── main.py  # PyPy用
│   │   │   └── gen.py
│   │   ├── a.rs         # ソースコード
│   │   ├── a_gen.rs     # カスタムケース生成コード
│   │   └── test/        # テストケース
│   │       ├── sample-1.in   # サンプルケース
│   │       ├── sample-1.out
│   │       ├── custom-1.in   # 生成したテストケース
│   │       └── custom-1.out
│   ├── arc/      # AtCoder Regular Contest
│   │   ├── contest.yaml
│   │   ├── template/
│   │   └── test/
│   └── ahc/      # AtCoder Heuristic Contest
│       ├── contest.yaml
│       ├── template/
│       └── test/
├── archive/      # 過去のコンテスト
│   ├── abc300/   # アーカイブされたABC
│   ├── arc164/   # アーカイブされたARC
│   └── ahc027/   # アーカイブされたAHC
├── target/        # ビルド成果物
├── Cargo.toml     # パッケージ設定
└── Cargo.lock     # 依存関係のロック
```

## 実行環境

### Docker環境
- CPU: 2コア
- メモリ: 1024MB
- Rust (5054): rust:1.70
- PyPy (5078): pypy:3.10
- 外部ツール: online-judge-tools, Cargo, Git

## インストール方法

1. Dockerのインストール
2. リポジトリのクローン
3. 以下のコマンドで環境構築:
```bash
docker compose up -d
```

## 使用方法

### コマンド体系
```bash
cph <contest_id> <language> <command> <problem_id> [options]
```

#### パラメータ
- contest_id: コンテストID（例：abc300）
- language: 使用言語
  - `rust`: Rust (.rs)
  - `pypy`: PyPy (.py)
  - 省略形: 一意に特定できる先頭文字列（例：`r`、`py`）
- command: 実行コマンド
  - `open`: 問題ファイルの作成とテストケース取得
  - `test`: テストケース実行
  - `submit`: AtCoderへの提出
  - 省略形: 一意に特定できる先頭文字列（例：`o`、`t`、`s`）
- problem_id: 問題ID（a, b, c, ...）

#### 使用例

1. コンテストへの参加（完全形）:
```bash
cph abc300 rust open a
```

2. コンテストへの参加（省略形）:
```bash
cph abc300 r o a
```

3. テストの実行:
```bash
cph abc300 r t a  # または cph abc300 rust test a
```

4. 解答の提出:
```bash
cph abc300 r s a  # または cph abc300 rust submit a
```

5. AHCのテスト実行:
```bash
cph ahc001 r ahctest 100
```

### contest.yaml
```yaml
contest:
  id: "abc300"
  url: "https://atcoder.jp/contests/abc300"
``` 