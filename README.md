# cph (Competitive Programming Helper)

競技プログラミングの問題を解くためのCLIツールです。

## 機能

- AtCoderへのログイン
- 問題の自動セットアップ
- テンプレートの自動生成
- エディタとブラウザでの問題ページの自動オープン

## インストール

```bash
cargo install --path .
```

## 使い方

### コマンドの構造

```bash
cph <SITE> <COMMAND> [ARGS...]

# 例：
cph atcoder login           # ログイン
cph atcoder work abc001    # コンテストの設定
cph atcoder open a         # 問題を開く
```

利用可能なコマンド：
- `login` (`l`): サイトにログイン
- `work` (`w`): コンテストの設定
- `open` (`o`): 問題を開く
- `language` (`lang`): 言語の設定
- `test` (`t`): テストを実行（予定）
- `submit` (`s`): 解答を提出（予定）
- `generate` (`g`): テストケースを生成（予定）

利用可能なサイト：
- `atcoder` (エイリアス: `at-coder`, `at_coder`)
- `codeforces` (エイリアス: `cf`)

利用可能な言語：
- `rust`
- `pypy`

### ログイン

AtCoderにログインします：

```bash
cph atcoder login
```

ログイン時に以下の情報を入力：
- ユーザー名
- パスワード

注意：
- ログイン情報は`online-judge-tools`によって安全に管理されます
- ログイン状態は`~/.local/share/online-judge-tools/cookie.jar`に保存されます

### コンテストの設定

コンテストを設定します：

```bash
cph atcoder work abc001
```

これにより：
1. 既存のファイルがアーカイブされます
2. 新しいコンテスト用の環境が設定されます

### 問題を開く

問題を開きます：

```bash
cph atcoder open a
```

これにより：
1. 問題用のファイルが作成されます
2. エディタで問題ファイルが開かれます
3. ブラウザで問題ページが開かれます

### 言語の設定

使用する言語を設定します：

```bash
cph atcoder language pypy
```

## ファイル構造

```
.
├── contests/          # アーカイブされたコンテスト
│   └── abc001/
│       └── a.rs
└── workspace/         # 現在のワークスペース
    ├── a.rs          # 現在の問題ファイル
    ├── contests.yaml # コンテスト設定
    └── .moveignore   # 移動対象外ファイルの設定
```

## 開発者向け情報

### テスト

基本的なテストを実行：

```bash
cargo test
```

### 手動テスト項目

以下の機能は手動でテストしてください：

1. ログイン機能
   - 正しいユーザー名とパスワードでログイン
   - 誤ったユーザー名やパスワードでログイン
   - ログイン状態の永続化

2. ブラウザ連携
   - 問題ページが正しく開かれるか
   - 適切なURLが生成されているか

3. エディタ連携
   - VSCodeまたはCursorで問題ファイルが開かれるか
   - テンプレートが正しく適用されているか 