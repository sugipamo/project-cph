# cph (Competitive Programming Helper)

競技プログラミングのためのCLIツール

## ディレクトリ構成

```
.
├── workspace/                # ユーザーのワークスペース
│   └── {contest_type}/      # コンテストタイプ (abc, arc, etc.)
│       ├── template/        # 言語ごとのテンプレート
│       ├── test/           # テストケース
│       └── {problem}.{ext}  # 問題ごとのソースコード
│
└── compile/                 # コンパイル用ワークスペース
    ├── rust/               # Rust用コンパイル環境
    │   ├── Cargo.toml     # Rustプロジェクト設定
    │   └── src/           # Rustソースコード
    │       └── main.rs    # コンパイル対象のコード
    │
    └── pypy/              # PyPy用実行環境
        └── main.py        # 実行対象のコード

```

## コンパイル環境

各言語ごとに独立したコンパイル環境を用意しています：

### Rust
- `compile/rust/`にCargoプロジェクトとして配置
- コンパイル対象のコードは`src/main.rs`として配置
- 必要なクレートは`Cargo.toml`で管理

### PyPy
- `compile/pypy/`に直接ソースコードを配置
- 実行対象のコードは`main.py`として配置

## 使用方法

1. 問題の作成
```bash
cph open abc001 a rust  # abc001のA問題をRustで解く
```

2. テストの実行
```bash
cph test abc001 a  # A問題のテストを実行
```

3. テストケースの生成
```bash
cph generate abc001 a  # A問題のテストケースを生成
```

4. 提出（未実装）
```bash
cph submit abc001 a  # A問題の解答を提出
``` 