# プロジェクト構造変更タスク

## 1. テンプレート構造の変更

### contest_template/の再構成
- [ ] 言語ごとのディレクトリ構造に変更
  ```
  contest_template/
  ├── pypy/
  │   ├── solution.py
  │   ├── generator.py
  │   └── .moveignore
  ├── rust/
  │   ├── solution.rs
  │   ├── generator.rs
  │   └── .moveignore
  └── cpp/
      ├── solution.cpp
      ├── generator.cpp
      └── .moveignore
  ```

### 設定ファイルの更新
- [ ] `src/config/languages.yaml`の更新
  - テンプレートパスの構造を新しい形式に対応
  - 言語ごとの.moveignoreの設定を追加

## 2. active_contest構造の変更

### ディレクトリ構造の変更
- [ ] 問題ごとのディレクトリ構造に変更
  ```
  active_contest/
  ├── a/
  │   ├── solution.py
  │   ├── generator.py
  │   ├── test/
  │   └── .moveignore
  ├── b/
  │   ├── solution.py
  │   ├── generator.py
  │   ├── test/
  │   └── .moveignore
  └── contests.yaml
  ```

## 3. コードの修正

### src/contest/mod.rs
- [ ] `get_source_path`メソッドの更新
  - 新しいディレクトリ構造に対応
  - 問題IDごとのディレクトリを考慮

### src/cli/commands/
- [ ] `open.rs`の修正
  - テストケースのダウンロード先を問題ディレクトリ内の`test/`に変更
- [ ] `generate.rs`の修正
  - 問題ディレクトリの作成処理を追加
  - テンプレートのコピー処理を新構造に対応
- [ ] `work.rs`の修正
  - 新しいディレクトリ構造でのファイル移動処理に対応

### src/oj/mod.rs
- [ ] `open`メソッドの修正
  - テストケースのダウンロードパスを問題ディレクトリ内に変更

## 4. テストの更新

### tests/
- [ ] `helpers/mod.rs`の更新
  - テスト用テンプレートディレクトリ構造の変更
- [ ] 統合テストの更新
  - 新しいディレクトリ構造に対応したテストケースの追加

## 5. ドキュメントの更新

### docs/
- [ ] `configuration.md`の更新
  - 新しいディレクトリ構造の説明を追加
  - テンプレートのカスタマイズ方法の更新
- [ ] `usage.md`の更新
  - 新しい使用方法の説明を追加

## 6. 移行スクリプト

### tools/
- [ ] 既存のプロジェクトを新構造に移行するスクリプトの作成
  - 既存の問題ファイルを新しいディレクトリ構造に移動
  - テストケースの移動
  - テンプレートの移行 