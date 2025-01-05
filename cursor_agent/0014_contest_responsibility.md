# Contest構造体の責務分析

## 現状の構造

```rust
pub struct Contest {
    #[serde(default)]
    pub active_contest_dir: PathBuf,
    pub contest_id: String,
    pub language: Option<String>,
    pub site_id: String,
    #[serde(skip)]
    workspace_dir: PathBuf,
    #[serde(skip)]
    config: Config,
}
```

## 主要な責務

1. コンテスト情報の管理
   - コンテストID
   - 使用言語
   - サイト情報
   - 作業ディレクトリ

2. ファイルシステム操作
   - テンプレートのコピー
   - ファイルの移動
   - パス解決
   - .moveignoreの管理

3. 設定管理
   - 設定の読み込み
   - 設定値の取得
   - エイリアス解決

4. URL生成
   - 問題URL
   - 提出URL

## 使用箇所

1. コマンド実行時の初期化
   - work
   - test
   - language
   - submit
   - generate

2. テスト実行
   - テストケースの生成
   - テストの実行

3. 提出処理
   - ソースファイルの取得
   - 言語情報の解決
   - 提出URLの生成

## 課題

1. 責務の混在
   - ファイルシステム操作と設定管理が密結合
   - URLの生成ロジックが混在

2. 状態管理の複雑さ
   - 必須フィールドと任意フィールドの区別が不明確
   - シリアライズ対象の選択が複雑

3. エラーハンドリング
   - エラーの種類が多岐にわたる
   - エラーメッセージの一貫性

## 改善案

1. 責務の分離
   ```rust
   // コンテスト情報の管理
   pub struct ContestInfo {
       pub id: String,
       pub language: Option<String>,
       pub site_id: String,
   }

   // ファイルシステム操作
   pub struct ContestFileSystem {
       pub active_dir: PathBuf,
       pub workspace_dir: PathBuf,
   }

   // URL生成
   pub struct ContestUrlGenerator {
       config: Config,
       site_id: String,
   }
   ```

2. Builder パターンの導入
   ```rust
   pub struct ContestBuilder {
       contest_id: Option<String>,
       language: Option<String>,
       site_id: Option<String>,
       config: Config,
   }
   ```

3. エラー型の整理
   ```rust
   #[derive(Error, Debug)]
   pub enum ContestError {
       #[error("設定エラー: {0}")]
       Config(String),
       #[error("ファイルシステムエラー: {0}")]
       FileSystem(String),
       #[error("URL生成エラー: {0}")]
       UrlGeneration(String),
   }
   ```

## 作業難易度
🔴 高

- 広範囲な変更が必要
- 既存のコマンド実装の修正が必要
- テストの大幅な追加/修正が必要

## 期待される効果

1. コードの保守性向上
   - 責務が明確に分離される
   - テストが書きやすくなる
   - エラーハンドリングが改善

2. 拡張性の向上
   - 新機能の追加が容易に
   - インターフェースがクリーンに

3. 信頼性の向上
   - エラーの種類が明確に
   - 状態管理が簡潔に 