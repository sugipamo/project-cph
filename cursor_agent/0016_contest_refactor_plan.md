# Contest構造体のリファクタリング計画

## 現状の課題

1. エラーハンドリング
   - エラーメッセージが文字列ベース
   - エラー型が統一されていない
   - エラーの種類が不明確

2. メソッドの分類
   - 関連するメソッドが散在
   - 責務の境界が不明確
   - ドキュメントが不足

3. 設定管理
   - 設定の取得方法が複数存在
   - エイリアス解決のロジックが重複
   - デフォルト値の扱いが不統一

## リファクタリング手順

### Phase 1: エラー型の整理

```rust
#[derive(Debug, Error)]
pub enum ContestError {
    #[error("設定エラー: {0}")]
    Config(String),
    
    #[error("ファイルシステムエラー: {0}")]
    FileSystem(String),
    
    #[error("言語エラー: {0}")]
    Language(String),
    
    #[error("サイトエラー: {0}")]
    Site(String),
}
```

### Phase 2: メソッドのグループ化

```rust
impl Contest {
    // 1. コンストラクタ系メソッド
    pub fn new(config: &Config, problem_id: &str) -> Result<Self>
    pub fn default() -> Self

    // 2. 設定系メソッド
    pub fn set_language(&mut self, language: &str) -> Result<()>
    pub fn set_site(&mut self, site_id: &str) -> Result<()>
    pub fn set_contest(&mut self, contest_id: String)
    pub fn save(&self) -> Result<()>

    // 3. パス解決系メソッド
    pub fn get_solution_path(&self, problem_id: &str) -> Result<PathBuf>
    pub fn get_generator_path(&self, problem_id: &str) -> Result<PathBuf>
    pub fn get_tester_path(&self, problem_id: &str) -> Result<PathBuf>

    // 4. ファイルシステム系メソッド
    pub fn create_problem_directory(&self, problem_id: &str) -> Result<()>
    fn copy_dir_contents(&self, source: &Path, target: &Path) -> Result<()>
    fn move_files_to_contests(&self) -> Result<()>

    // 5. URL生成系メソッド
    pub fn get_problem_url(&self, problem_id: &str) -> Result<String>
    pub fn get_submit_url(&self, problem_id: &str) -> Result<String>

    // 6. 設定アクセス系メソッド
    pub fn get_config<T: TypedValue>(&self, path: &str) -> Result<T>
    fn get_language_config<T: TypedValue>(&self, config_path: &str) -> Result<T>
}
```

### Phase 3: ドキュメント整備

1. 構造体フィールドの説明
   ```rust
   /// コンテスト情報を管理する構造体
   #[derive(Debug, Clone, Serialize, Deserialize)]
   pub struct Contest {
       /// アクティブなコンテストのディレクトリ
       #[serde(default)]
       pub active_contest_dir: PathBuf,
       
       /// コンテストID
       pub contest_id: String,
       
       /// 使用言語
       pub language: Option<String>,
       
       /// サイトID
       pub site_id: String,
       
       /// ワークスペースのルートディレクトリ
       #[serde(skip)]
       workspace_dir: PathBuf,
       
       /// 設定情報
       #[serde(skip)]
       config: Config,
   }
   ```

2. メソッドのドキュメント
   - 引数の説明
   - 戻り値の説明
   - エラーケースの説明
   - 使用例の追加

## 作業順序

1. エラー型の整理
   - `ContestError`の実装
   - 既存エラーの移行
   - エラーメッセージの改善

2. メソッドの整理
   - 関連メソッドのグループ化
   - 不要なパブリックメソッドの整理
   - インターフェースの統一

3. ドキュメントの追加
   - 構造体の説明
   - メソッドの説明
   - 使用例の追加

## 期待される効果

1. エラーハンドリングの改善
   - エラーの種類が明確に
   - エラーメッセージの一貫性
   - デバッグが容易に

2. コードの可読性向上
   - 関連する機能が集約
   - 責務の境界が明確
   - メンテナンスが容易

3. 使いやすさの向上
   - ドキュメントの充実
   - エラーメッセージの改善
   - 型安全性の向上 