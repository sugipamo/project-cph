## 言語設定のハードコード箇所

### 1. `src/lib.rs`
- `Language` enumにRustとPyPyのみがハードコードされている（15-21行目）
- 言語IDがハードコードされている（59-64行目）
  - AtCoderのRust: "5054"
  - AtCoderのPyPy: "5078"
- 言語拡張子がハードコードされている（52-57行目）
  - Rust: "rs"
  - PyPy: "py"
- デフォルトのテンプレートパスがハードコードされている（68-70行目）

### 2. `src/cli/commands/generate.rs`
- テンプレート拡張子のマッピングがハードコードされている（31-36行目）
  - python: "py"
  - cpp: "cpp"
  - rust: "rs"

### 改善案
1. 設定ファイルの分割（`~/.config/cph/`配下）
   a. `commands.yaml` - コマンドのエイリアス設定
   ```yaml
   commands:
     test:
       - t
       - check
     open:
       - o
       - show
     submit:
       - s
       - sub
     init:
       - i
       - create
     language:
       - l
       - lang
     login:
       - auth
   ```

   b. `languages.yaml` - 言語関連の設定
   ```yaml
   languages:
     python:
       aliases:
         - Python
         - python3
       extension: "py"
       templates:
         default: "template/main.py"
         competitive: "template/competitive.py"
       site_ids:
         atcoder: "4006"  # Python (CPython 3.11.4)
     
     rust:
       aliases:
         - Rust
         - rs
       extension: "rs"
       templates:
         default: "template/main.rs"
         competitive: "template/competitive.rs"
       site_ids:
         atcoder: "5054"  # Rust (rustc 1.70.0)
   ```

   c. `sites.yaml` - サイト関連の設定
   ```yaml
   sites:
     atcoder:
       aliases:
         - at-coder
         - at_coder
         - AtCoder
         - ac
       url_pattern: "https://atcoder.jp/contests/{contest_id}/tasks/{problem_id}"
       supported_languages:
         - python
         - rust
         - cpp
   ```

2. 実装手順
   a. 設定ファイルの分割（第一段階）
   - `src/config/`に新しい設定ファイルを作成
   - 既存の`aliases.yaml`から各設定を移行
   - 設定読み込みのための新しい構造体を作成:
     - `CommandConfig`
     - `LanguageConfig`
     - `SiteConfig`

   b. 設定読み込みロジックの更新（第二段階）
   - `src/config/mod.rs`の作成
   - 各設定ファイルの読み込み処理の実装
   - バリデーション機能の実装
   - エラーハンドリングの整備

   c. ハードコード解消（第三段階）
   - `Language` enumの動的生成
   - 言語ID、拡張子の設定ファイルからの読み込み
   - テンプレートパスの動的解決

3. 影響範囲と更新順序
   a. 設定関連
   - `src/config/aliases.rs` → `src/config/mod.rs`に統合
   - 新規: `src/config/commands.rs`
   - 新規: `src/config/languages.rs`
   - 新規: `src/config/sites.rs`

   b. 機能関連
   - `src/lib.rs`: 言語enum生成の動的化
   - `src/cli/commands/generate.rs`: テンプレート処理の更新
   - `src/cli/commands/language.rs`: 言語設定処理の更新 