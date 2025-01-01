# Contest構造体の責務再考

## 前回の提案の問題点

1. 過度な分割による複雑化
   - 構造体の増加による依存関係の複雑化
   - 各構造体間の状態同期の必要性
   - インターフェースの増加によるメンテナンスコストの上昇

2. コンテキストの分断
   - コンテスト情報とファイルシステムは密接に関連
   - URL生成にはコンテスト情報とサイト情報の両方が必要
   - 分割による情報の重複保持

3. 実装の複雑化
   - Builder パターンによる初期化の冗長化
   - エラーハンドリングの複雑化
   - テストの難易度上昇

## 現状の Contest 構造体の利点

1. 凝集度の高さ
   - コンテスト関連の情報が一箇所に集約
   - 状態管理が明確
   - 依存関係が単純

2. 使いやすさ
   - コマンド実装からの利用が容易
   - メソッドチェーンによる操作が可能
   - エラーハンドリングが統一的

3. 拡張性
   - 新しいフィールドの追加が容易
   - 機能追加時の影響範囲が明確
   - 既存のコードとの互換性維持が容易

## 改善の方向性

1. 内部構造の整理
   ```rust
   pub struct Contest {
       // コアとなるコンテスト情報
       pub contest_id: String,
       pub site_id: String,
       pub language: Option<String>,

       // ファイルシステム関連
       #[serde(default)]
       pub active_contest_dir: PathBuf,
       #[serde(skip)]
       workspace_dir: PathBuf,

       // 設定関連
       #[serde(skip)]
       config: Config,
   }
   ```

2. メソッドの整理
   ```rust
   impl Contest {
       // コンテスト情報関連
       pub fn with_language(mut self, language: &str) -> Result<Self>
       pub fn with_site(mut self, site_id: &str) -> Result<Self>

       // ファイルシステム関連
       pub fn get_solution_path(&self, problem_id: &str) -> Result<PathBuf>
       pub fn get_test_path(&self, problem_id: &str) -> Result<PathBuf>

       // URL生成関連
       pub fn get_problem_url(&self, problem_id: &str) -> Result<String>
       pub fn get_submit_url(&self, problem_id: &str) -> Result<String>
   }
   ```

3. エラー型の整理
   ```rust
   #[derive(Error, Debug)]
   pub enum ContestError {
       #[error("{0}")]
       Generic(String),
       
       #[error("設定エラー: {0}")]
       Config(String),
   }
   ```

## 作業難易度
🟡 中

- 既存構造体の内部整理が主
- メソッドの再編成
- エラー型の統合

## 期待される効果

1. コードの見通しの向上
   - 関連する情報が適切にグループ化
   - メソッドの責務が明確
   - エラーハンドリングがシンプル

2. メンテナンス性の向上
   - 変更の影響範囲が予測可能
   - テストが書きやすい
   - デバッグが容易

3. 使いやすさの維持
   - 既存のインターフェースを維持
   - 段階的な改善が可能
   - 学習コストの最小化 