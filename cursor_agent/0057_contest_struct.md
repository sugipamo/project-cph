# コンテストモジュール構造体と機能まとめ

## 1. Contest構造体
コンテスト情報を管理する中心的な構造体

### 主要フィールド
- state: ContestState - コンテストの状態
- config: Arc<Config> - 設定情報
- fs_manager: Arc<FileManager> - ファイル操作マネージャー

### 主要機能
- サイト認証用のインスタンス作成
- 新規コンテストインスタンス作成
- 状態管理
- 設定管理
- ファイル操作

## 2. ContestState構造体
コンテストの状態を管理する構造体

### フィールド
- active_contest_dir: PathBuf - アクティブなコンテストのディレクトリ
- contest: String - コンテスト情報
- problem: Option<String> - 問題ID
- language: Option<String> - 使用言語
- site: String - サイトID（atcoder, codeforcesなど）

### 機能
- 問題ID設定
- 言語設定
- コンテストID設定
- サイト設定
- アクティブディレクトリ設定

## 3. PathResolver構造体
パス解決を担当する構造体

### 主要機能
- テンプレートディレクトリのパス取得
- コンテスト保存用ディレクトリのパス取得
- 問題ファイルのパス取得
- ソリューションファイルのパス取得
- ジェネレータファイルのパス取得
- テスターファイルのパス取得
- テストディレクトリのパス取得
- ディレクトリ内容の再帰的コピー

## 4. TestManager構造体
テスト関連の機能を提供する構造体

### フィールド
- test_dir: PathBuf - テストディレクトリ
- generator_path: PathBuf - ジェネレータファイルのパス
- tester_path: PathBuf - テスターファイルのパス
- language: String - 使用言語

### 機能
- テストの生成
- テストの実行
- テストディレクトリの管理

## 5. UrlGenerator構造体
URL生成を担当する構造体

### フィールド
- site: String - サイトID
- contest: String - コンテストID
- config: Config - 設定情報

### 機能
- サイトURLの生成
- 問題URLの取得
- 提出URLの取得 