# 使用方法

## コマンド構造

```bash
cph <SITE> <COMMAND> [ARGS...]
```

### 利用可能なサイト
- `atcoder` (エイリアス: `at-coder`, `at_coder`)

### 基本コマンド

1. **login**: サイトにログイン
```bash
cph atcoder login
```

2. **work** (`w`): コンテストの設定
```bash
cph atcoder work abc001
```

3. **open** (`o`): 問題を開く
```bash
cph atcoder open a
```

4. **language** (`l`): 言語の設定
```bash
# Rust
cph atcoder language rust

# PyPy
cph atcoder language pypy
```

5. **test** (`t`): テストを実行
```bash
cph atcoder test a
```

6. **submit** (`s`): 解答を提出
```bash
cph atcoder submit a
```

## 詳細な使用例

### 1. ログイン
```bash
cph atcoder login
```
- ユーザー名とパスワードを入力
- ログイン情報は`~/.local/share/online-judge-tools/cookie.jar`に安全に保存

### 2. コンテストの設定
```bash
cph atcoder work abc001
```
実行結果：
1. 既存のファイルが`contests/abc001/`ディレクトリに移動
2. 新しいコンテスト用の環境が`active_contest`に設定

### 3. 問題を開く
```bash
cph atcoder open a
```
実行結果：
1. 問題用のディレクトリ`active_contest/a/`が作成
2. テンプレートファイルがコピー
   - Rust: `solution.rs`
   - PyPy: `solution.py`
3. エディタで問題ファイルが開く
4. ブラウザで問題ページが開く
5. テストケースが`test/`ディレクトリにダウンロード

### 4. テストの実行
```bash
cph atcoder test a
```
テスト機能：
- メモリ制限（デフォルト: 256MB）
- タイムアウト処理（デフォルト: 30秒）
- 並列テスト実行
- テスト結果の詳細表示

### 5. 解答の提出
```bash
cph atcoder submit a
```
提出前の動作：
1. テストの自動実行
2. テスト成功時のみ提出

## エラーメッセージについて

エラー表示の特徴：
- 構造化されたメッセージ
- コンパイルエラーの色付き表示
- エラー位置の強調表示
- 言語固有のエラー情報
  - Rust: エラーコードへのドキュメントリンク
  - C++: エラー行番号とメッセージ
  - PyPy: トレースバック情報

## ディレクトリ構造

問題ディレクトリ（例：`active_contest/a/`）：
```
a/
├── solution.{ext}  # メインの解答ファイル
├── generator.{ext} # テストケース生成（オプション）
└── test/          # ダウンロードされたテストケース
```

## テンプレートのカスタマイズ

テンプレートファイルの場所：
- Rust: `contest_template/rust/solution.rs`
- PyPy: `contest_template/pypy/solution.py`
- C++: `contest_template/cpp/solution.cpp`

カスタマイズ方法：
1. 対応する言語のディレクトリ内のファイルを編集
2. 次回の問題作成時から新しいテンプレートが適用 