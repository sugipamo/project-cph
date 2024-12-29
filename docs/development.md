# 開発者向け情報

## プロジェクト構造

主要なディレクトリとファイル：

```
src/
├── bin/
│   └── cph.rs          # エントリーポイント
├── cli/
│   └── commands/       # コマンド実装
│       ├── generate.rs
│       ├── language.rs
│       ├── login.rs
│       ├── mod.rs
│       ├── open.rs
│       ├── submit.rs
│       ├── test.rs
│       └── work.rs
├── contest/
│   └── mod.rs          # コンテスト関連の処理
├── docker/
│   └── runner/         # Dockerでのテスト実行
├── workspace/
│   └── mod.rs          # ワークスペース管理
└── lib.rs              # ライブラリのルート

tests/                  # テストファイル
└── integration/        # 統合テスト
```

## 開発環境のセットアップ

1. リポジトリのクローン：
```bash
git clone [リポジトリURL]
cd cph
```

2. 依存関係のインストール：
- Rust toolchain
- Docker
- VSCode または Cursor

3. ビルドとテスト：
```bash
cargo build
cargo test
```

## テスト

### 単体テスト
```bash
cargo test
```

### 統合テスト
```bash
cargo test --test '*'
```

### 手動テスト項目

1. ログイン機能
   - 正しいユーザー名とパスワードでログイン
   - 誤ったユーザー名やパスワードでログイン
   - ログイン状態の永続化

2. ブラウザ連携
   - 問題ページが正しく開かれるか
   - 適切なURLが生成されているか

3. エディタ連携
   - VSCode/Cursorで問題ファイルが開かれるか
   - テンプレートが正しく適用されているか

## コーディング規約

1. Rustフォーマット
```bash
cargo fmt
```

2. Lint
```bash
cargo clippy
```

3. ドキュメント
- 公開関数には必ずドキュメントコメントを付ける
- 複雑なロジックには説明コメントを付ける

## プルリクエストの手順

1. 新しいブランチを作成：
```bash
git checkout -b feature/your-feature-name
```

2. 変更を加える：
- コードスタイルを既存のコードに合わせる
- 必要に応じてテストを追加
- ドキュメントを更新

3. テストの実行：
```bash
cargo test
cargo fmt -- --check
cargo clippy
```

4. 変更をコミット：
```bash
git commit -m "feat: 変更内容の説明"
```

5. プルリクエストを作成：
- 変更内容を詳しく説明
- 関連するイシューがあれば参照

## リリース手順

1. バージョン番号の更新：
- `Cargo.toml`のバージョンを更新
- CHANGELOGを更新

2. テストの実行：
```bash
cargo test
cargo fmt -- --check
cargo clippy
```

3. タグの作成：
```bash
git tag -a v0.1.0 -m "バージョン0.1.0"
git push origin v0.1.0
```

4. リリースの作成：
- GitHubでリリースを作成
- バイナリを添付
- 変更点を記載 