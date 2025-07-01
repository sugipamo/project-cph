# CPH (Competitive Programming Helper)

競技プログラミングを支援するCLIツールです。問題の管理、テストケースの実行、ソリューションの提出をサポートします。

## インストール

```bash
# ソースからビルド
git clone https://github.com/your-username/cph.git
cd cph/rust
cargo build --release
```

## 使い方

### 問題を開く

新しい問題のディレクトリを作成し、テンプレートファイルを生成します。

```bash
cph open abc001a
# URLを指定することも可能
cph open abc001a --url https://atcoder.jp/contests/abc001/tasks/abc001_1
```

これにより以下が作成されます：
- `abc001a/` - 問題ディレクトリ
- `abc001a/main.rs` - ソリューション用テンプレート
- `abc001a/sample/` - テストケース用ディレクトリ

### テストを実行

問題ディレクトリ内でテストケースを実行します。

```bash
cd abc001a
cph test
```

テストケースは `sample/` ディレクトリに配置します：
- `1.in` - 入力例1
- `1.out` - 期待される出力1
- `2.in`, `2.out`, ... （必要に応じて追加）

### ソリューションを提出

提出前の検証を行います（実際の提出は今後実装予定）。

```bash
cph submit abc001a
# ファイルを指定することも可能
cph submit abc001a --file solution.rs
```

### ワークスペースの初期化

競技プログラミング用のワークスペースを初期化します（今後実装予定）。

```bash
cph init
```

## 設定

環境変数でデバッグレベルを設定できます：

```bash
RUST_LOG=debug cph test
```

## 開発

### ビルド

```bash
cargo build
```

### テスト

```bash
cargo test
```

### コード品質チェック

```bash
cargo clippy
cargo fmt
```

## ライセンス

MIT License