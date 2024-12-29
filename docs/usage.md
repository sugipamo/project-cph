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
1. 既存のファイルが`contests`ディレクトリに移動
2. 新しいコンテスト用の環境が設定

### 3. 問題を開く
```bash
cph atcoder open a
```
実行結果：
1. 問題用のファイルが作成
2. エディタで問題ファイルが開く
3. ブラウザで問題ページが開く

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
- Rustエラーコードへのドキュメントリンク

## テンプレートのカスタマイズ

テンプレートファイルの場所：
- Rust: `template/main.rs`
- PyPy: `template/main.py`

カスタマイズ方法：
1. テンプレートファイルを編集
2. 次回の問題作成時から新しいテンプレートが適用 