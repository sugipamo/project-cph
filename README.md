# cph (Competitive Programming Helper)

競技プログラミングの問題を解くためのCLIツールです。

## 機能

### 実装済み機能
- AtCoderへのログイン
- 問題の自動セットアップ
- テンプレートの自動生成
- エディタとブラウザでの問題ページの自動オープン
- 基本的なテスト実行（メモリ制限、タイムアウト処理付き）
- エラーメッセージの構造化表示
- 解答の提出（テスト実行付き）

### 開発中の機能
- テストケース生成
- AHCツール対応

## インストール

### 必要な依存関係

1. Rust toolchain
   ```bash
   curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
   ```

2. Docker
   - [Docker Desktop](https://www.docker.com/products/docker-desktop/)をインストール
   - または以下のコマンドでインストール:
     ```bash
     curl -fsSL https://get.docker.com | sh
     ```

3. online-judge-tools
   ```bash
   pip3 install online-judge-tools
   ```

4. VSCode または Cursor
   - [Visual Studio Code](https://code.visualstudio.com/)
   - [Cursor](https://cursor.sh/)

### cphのインストール

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
cph atcoder language pypy # 言語の設定
cph atcoder test a         # テストを実行
cph atcoder submit a       # 解答を提出
```

利用可能なコマンド：
- `login` (`l`): サイトにログイン
- `work` (`w`): コンテストの設定
- `open` (`o`): 問題を開く
- `language` (`lang`): 言語の設定
- `test` (`t`): テストを実行
- `submit` (`s`): 解答を提出
- `generate` (`g`): テストケースを生成（開発中）

利用可能なサイト：
- `atcoder` (エイリアス: `at-coder`, `at_coder`)

現時点で利用可能な言語：
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

## 今後のドキュメント整備予定

以下のドキュメントの拡充を予定しています：

1. インストール手順の詳細化
   - 依存関係の説明
   - トラブルシューティング

2. コマンドガイド
   - 各コマンドの詳細な使用例
   - オプションの説明

3. トラブルシューティング
   - よくある問題と解決方法
   - エラーメッセージの説明 

## テスト機能

現在実装されているテスト機能：

- メモリ制限（デフォルト: 256MB）
- タイムアウト処理（デフォルト: 30秒）
- 並列テスト実行
- テスト結果の詳細表示
- コンパイルエラーの強調表示
- ランタイムエラーのスタックトレース表示

## エラーハンドリング

現在実装されているエラー処理：

- 構造化されたエラーメッセージ
- コンパイルエラーの色付き表示
- エラー位置の強調表示
- Rustエラーコードへのドキュメントリンク 

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。詳細は[LICENSE](LICENSE)ファイルを参照してください。

## 謝辞

このプロジェクトは以下のオープンソースソフトウェアを使用しています：

- [online-judge-tools](https://github.com/online-judge-tools/oj): MITライセンス
- [proconio](https://github.com/statiolake/proconio-rs): MITライセンス 

## コントリビューション

プロジェクトへの貢献を歓迎します！以下の方法で貢献できます：

1. イシューの報告
   - バグの報告
   - 新機能の提案
   - ドキュメントの改善提案

2. プルリクエストの作成
   - バグ修正
   - 新機能の追加
   - ドキュメントの改善
   - テストの追加

### 開発環境のセットアップ

1. リポジトリのクローン
   ```bash
   git clone https://github.com/sugipamo/project-cph.git
   cd project-cph
   ```

2. 依存関係のインストール
   - 上記の「必要な依存関係」セクションを参照

3. ビルドとテスト
   ```bash
   cargo build
   cargo test
   ```

### プルリクエストの手順

1. 新しいブランチを作成
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. 変更を加える
   - コードスタイルを既存のコードに合わせる
   - 必要に応じてテストを追加
   - ドキュメントを更新

3. テストの実行
   ```bash
   cargo test
   cargo fmt -- --check
   cargo clippy
   ```

4. 変更をコミット
   ```bash
   git commit -m "feat: 変更内容の説明"
   ```

5. プルリクエストを作成
   - 変更内容を詳しく説明
   - 関連するイシューがあれば参照 