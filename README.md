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

### ログイン

AtCoderにログインします：

```bash
cph atcoder login
```

または短縮形：

```bash
cph atcoder l
```

ログイン時に以下の情報を入力：
- ユーザー名
- パスワード

注意：
- ログイン情報は`online-judge-tools`によって安全に管理されます
- ログイン状態は`~/.local/share/online-judge-tools/cookie.jar`に保存されます

### 問題のセットアップ

新しい問題の環境をセットアップします：

```bash
cph atcoder abc001 rust open a
```

これにより：
1. 既存のファイルがアーカイブされます
2. 新しい問題用のファイルが作成されます
3. エディタで問題ファイルが開かれます
4. ブラウザで問題ページが開かれます

### コマンドの構造

```bash
cph <SITE> [CONTEST_ID] [LANGUAGE] <COMMAND> [PROBLEM_ID]

# 例：
cph atcoder login                      # ログイン
cph atcoder abc001 rust open a         # 問題を開く
```

利用可能なサマンド：
- `login` (`l`): サイトにログイン
- `open` (`o`): 問題を開く
- `test` (`t`): テストを実行（予定）
- `submit` (`s`): 解答を提出（予定）
- `generate` (`g`): テストケースを生成（予定）

利用可能なサイト：
- `atcoder` (エイリアス: `at-coder`, `at_coder`)
- `codeforces` (エイリアス: `cf`)

利用可能な言語：
- `rust`
- `pypy`

## TODO

- [ ] テストケースの実行機能
  - `cph atcoder abc001 rust test a`でテストを実行
  - サンプルケースの自動取得と実行
  - 実行時間と使用メモリの表示

- [ ] テストケースの生成機能
  - `cph atcoder abc001 rust generate a`でテストケースを生成
  - ランダムケースの生成
  - エッジケースの自動生成

- [ ] 解答の提出機能
  - `cph atcoder abc001 rust submit a`で解答を提出
  - 提出前の最終確認
  - 提出結果の表示

- [ ] 追加サイト対応
  - yukicoder対応
  - その他のコンテストサイト対応

- [ ] AHC機能
  - ビジュアライザの統合
  - ローカルテスト機能
  - スコア計算機能

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