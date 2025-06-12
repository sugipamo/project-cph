# Contest Environment Configuration Specification

## 概要

このドキュメントは、競技プログラミング支援ツール（cph.sh）の環境設定仕様について説明します。

## 設定ファイル構造

```
contest_env/
├── shared/env.json     # 全言語共通設定
├── python/env.json     # Python固有設定
├── rust/env.json       # Rust固有設定
└── cpp/env.json        # C++固有設定
```

## 1. 共通設定 (shared/env.json)

### 1.1 パス設定 (paths)

| パス名 | 説明 | デフォルト値 |
|--------|------|-------------|
| `contest_current_path` | 現在作業中のコンテスト問題のパス | `./contest_current` |
| `contest_stock_path` | 保存済み作業のストックパス | `./contest_stock/{language_name}/{contest_name}/{problem_name}` |
| `contest_template_path` | テンプレートファイルのパス | `./contest_template` |
| `contest_temp_path` | 一時ファイル用パス | `./.temp` |
| `workspace_path` | 実行・テスト用ワークスペースパス | `./workspace` |

### 1.2 コマンド設定 (commands)

#### 1.2.1 openコマンド
**説明**: 問題を開く（切り替え・復元も自動処理）  
**エイリアス**: `["o"]`

**実行ステップ**:
1. **contest_stockから復元**: 既存の作業がある場合、自動復元
2. **テンプレートから初期化**: 新規問題の場合、テンプレートから初期化
3. **ブラウザで問題を開く**: AtCoderの問題ページをブラウザで表示
4. **エディタでファイルを開く**: Cursorエディタでソースファイルを開く
5. **テストケースをダウンロード**: online-judge-toolsでテストケースを取得
6. **テストケースを移動**: ダウンロードしたテストケースを適切な場所に配置

#### 1.2.2 testコマンド
**説明**: テストを実行する  
**エイリアス**: `["t"]`

**実行ステップ**:
1. **ソースファイルをワークスペースにコピー**: 現在のソースをワークスペースにコピー
2. **テスト実行**: 指定された実行コマンドでテストを実行

#### 1.2.3 submitコマンド
**説明**: 提出する  
**エイリアス**: `["s"]`

**実行ステップ**:
1. **ソースファイルをワークスペースにコピー**: 現在のソースをワークスペースにコピー
2. **online-judgeで提出**: ojツールを使用してAtCoderに提出

#### 1.2.4 backupコマンド
**説明**: 現在の作業をcontest_stockにバックアップ  
**エイリアス**: `["b"]`

**実行ステップ**:
1. **バックアップ先ディレクトリを作成**: 必要に応じてディレクトリ作成
2. **既存のバックアップを削除**: 上書き保存のため既存削除
3. **contest_currentをバックアップ**: 現在の作業をバックアップ

#### 1.2.5 switchコマンド
**説明**: 問題を切り替え（自動バックアップ・復元）  
**エイリアス**: `["sw"]`

**実行ステップ**:
1. **現在の作業をバックアップ**: 現在の作業を自動保存
2. **contest_currentを削除**: 作業領域をクリア
3. **新しい問題のストックから復元**: 指定問題の作業を復元
4. **テンプレートから初期化**: 新規問題の場合、テンプレートから初期化

### 1.3 環境タイプ設定 (env_types)

| 環境 | エイリアス | 説明 |
|------|------------|------|
| `local` | `["local"]` | ローカル環境での実行 |
| `docker` | `["docker"]` | Docker環境での実行 |

### 1.4 出力設定 (output)

| 設定項目 | デフォルト | 説明 |
|----------|------------|------|
| `show_workflow_summary` | `true` | ワークフロー概要の表示 |
| `show_step_details` | `false` | ステップ詳細の表示 |
| `show_execution_completion` | `true` | 実行完了通知の表示 |

### 1.5 出力プリセット (output_presets)

| プリセット | 説明 |
|------------|------|
| `quiet` | 最小限の出力 |
| `summary_only` | サマリーのみ表示 |
| `minimal_details` | 最小限の詳細表示 |
| `verbose` | 詳細な出力 |

### 1.6 フォーマットプリセット (format_presets)

| プリセット | 説明 | 用途 |
|------------|------|------|
| `minimal` | 最小限の出力 | シンプルな結果表示 |
| `standard` | 標準的なフォーマット | 一般的な使用 |
| `competitive` | 競技プログラミング向け詳細フォーマット | 詳細な実行時間・結果表示 |
| `compact` | コンパクトな表示 | 省スペース表示 |

## 2. 言語固有設定

### 2.1 Python (python/env.json)

| 項目 | 値 | 説明 |
|------|-----|------|
| `aliases` | `["py"]` | 言語エイリアス |
| `language_id` | `"5078"` | AtCoderの言語ID |
| `source_file_name` | `"main.py"` | メインソースファイル名 |
| `run_command` | `"python3"` | 実行コマンド |

**ファイルパターン**:
- `test_files`: `["test/*.in", "test/*.out"]`
- `contest_files`: `["main.py", "*.py"]`
- `build_files`: `["__pycache__/**/*", "*.pyc", "*.pyo", ".pytest_cache/**/*"]`

### 2.2 Rust (rust/env.json)

| 項目 | 値 | 説明 |
|------|-----|------|
| `aliases` | `["rs"]` | 言語エイリアス |
| `language_id` | `"5054"` | AtCoderの言語ID |
| `source_file_name` | `"src/main.rs"` | メインソースファイル名 |
| `run_command` | 未設定 | 実行コマンド |

**ファイルパターン**:
- `test_files`: `["test/*.in", "test/*.out"]`
- `contest_files`: `["src/main.rs", "src/*.rs", "Cargo.toml"]`
- `build_files`: `["target/**/*", "Cargo.lock"]`

### 2.3 C++ (cpp/env.json)

| 項目 | 値 | 説明 |
|------|-----|------|
| `aliases` | `["c++", "cpp"]` | 言語エイリアス |
| `language_id` | `"5003"` | AtCoderの言語ID |
| `source_file_name` | `"main.cpp"` | メインソースファイル名 |
| `run_command` | 未設定 | 実行コマンド |

**ファイルパターン**:
- `test_files`: `["test/*.in", "test/*.out"]`
- `contest_files`: `["main.cpp", "*.cpp", "*.hpp", "*.h"]`
- `build_files`: `["*.o", "*.exe", "a.out", "main"]`

## 3. コマンド実行仕様

### 3.1 引数の順序
コマンド引数は**順不同**で受け入れられます。システムが引数を解析して適切に処理します。

**例**:
```bash
# 以下はすべて同等
./cph.sh abc300 open a python local
./cph.sh open abc300 a local python
./cph.sh local python abc300 a open
```

### 3.2 省略時の動作
- **問題名省略**: 前回値を使用
- **言語省略**: 前回値または設定デフォルトを使用
- **環境タイプ省略**: デフォルト環境を使用

### 3.3 変数展開
設定ファイル内では以下の変数が使用可能:
- `{language_name}`: 言語名
- `{contest_name}`: コンテスト名
- `{problem_name}`: 問題名
- `{source_file_name}`: ソースファイル名
- `{contest_files}`: コンテストファイルパターン
- `{test_files}`: テストファイルパターン
- `{run_command}`: 実行コマンド
- `{language_id}`: AtCoderの言語ID

## 4. E2Eテスト仕様

E2Eテスト (`scripts/e2e.py`) は以下のシナリオで動作確認を行います:

### 4.1 テストシナリオ

1. **ABC300問題A(Python)をオープン**: 新規問題の初期化テスト
2. **ファイル変更**: テンプレートとの差分作成
3. **ABC301問題A切り替え**: 問題切り替え・自動バックアップテスト
4. **ファイル内容確認**: 自動バックアップの動作確認
5. **テスト実行**: テスト機能の動作確認
6. **ABC300問題A再オープン**: 復元機能のテスト
7. **復元内容確認**: バックアップ・復元の整合性確認

### 4.2 検証項目

- テストファイル (`test/*.in`) の存在確認
- ソースファイルの自動復元確認
- バックアップ・復元の整合性確認
- コマンド実行の成功確認

## 5. ディレクトリ構造

### 5.1 実行時ディレクトリ構造
```
project-cph/
├── contest_current/           # 現在の作業ディレクトリ
│   ├── main.py               # メインソースファイル
│   └── test/                 # テストケース
│       ├── sample-1.in
│       ├── sample-1.out
│       └── ...
├── contest_stock/            # バックアップディレクトリ
│   └── {language}/{contest}/{problem}/
├── contest_template/         # テンプレートディレクトリ
│   └── {language}/
├── workspace/               # 実行用ワークスペース
└── cph_history.db          # 履歴データベース
```

### 5.2 設定ファイル継承
- **shared/env.json**: 全言語共通設定（ベース）
- **{language}/env.json**: 言語固有設定（上書き・追加）

## 6. セキュリティ・制限事項

### 6.1 実行制限
- タイムアウト: 300秒（デフォルト）
- リトライ設定: 最大3回、指数バックオフ

### 6.2 ファイル操作制限
- 指定ディレクトリ外への書き込み禁止
- システムファイルへのアクセス禁止

---

*このドキュメントは設定ファイルの実装と整合性を保つよう定期的に更新される必要があります。*