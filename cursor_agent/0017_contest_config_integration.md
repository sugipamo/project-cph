# Contest構造体とConfig構造体の統合

## 基本方針

1. Config構造体の役割
   - 設定ファイルの読み込み
   - 設定値の型安全な取得
   - エイリアス解決
   - 環境変数のフォールバック

2. Contest構造体の役割
   - コンテスト固有の状態管理
   - ファイルシステム操作
   - パス解決（Configを利用）
   - テスト実行制御

## 具体的な変更点

### 1. パス解決の整理

```rust
impl Contest {
    /// テストディレクトリのパスを取得
    pub fn get_test_dir(&self, problem_id: &str) -> Result<PathBuf> {
        let test_dir = self.config.get::<String>("system.test.dir")
            .map_err(|e| ContestError::Config(e.to_string()))?;
        Ok(self.active_contest_dir.join(problem_id).join(test_dir))
    }

    /// 問題ファイルのパスを取得
    fn get_problem_file_path(&self, problem_id: &str, file_type: &str) -> Result<PathBuf> {
        let language = self.language.as_ref()
            .ok_or_else(|| ContestError::Language("言語が設定されていません".into()))?;

        // 拡張子を取得
        let extension = self.config.get::<String>(&format!("languages.{}.extension", language))
            .map_err(|e| ContestError::Language(e.to_string()))?;

        // パターンを取得
        let pattern = self.config.get::<String>(&format!("system.templates.patterns.{}", file_type))
            .map_err(|e| ContestError::Config(e.to_string()))?;

        let file_name = pattern.replace("{extension}", &extension);
        Ok(self.active_contest_dir.join(problem_id).join(file_name))
    }
}
```

### 2. テンプレート関連の整理

```rust
impl Contest {
    /// 問題ディレクトリを作成し、テンプレートをコピー
    pub fn create_problem_directory(&self, problem_id: &str) -> Result<()> {
        let language = self.language.as_ref()
            .ok_or_else(|| ContestError::Language("言語が設定されていません".into()))?;

        // テンプレートディレクトリのパスを生成
        let template_pattern = self.config.get::<String>("system.templates.directory")
            .map_err(|e| ContestError::Config(e.to_string()))?;
        let template_base = self.config.get::<String>("system.contest_dir.template")
            .map_err(|e| ContestError::Config(e.to_string()))?;

        let template_dir_name = template_pattern.replace("{name}", language);
        let template_dir = self.workspace_dir.join(&template_base).join(template_dir_name);

        // 問題ディレクトリを作成
        let problem_dir = self.active_contest_dir.join(problem_id);
        if !problem_dir.exists() {
            fs::create_dir_all(&problem_dir)
                .map_err(|e| ContestError::FileSystem(e.to_string()))?;
        }

        // テストディレクトリを作成
        let test_dir = self.get_test_dir(problem_id)?;
        if !test_dir.exists() {
            fs::create_dir_all(&test_dir)
                .map_err(|e| ContestError::FileSystem(e.to_string()))?;
        }

        // テンプレートをコピー
        self.copy_dir_contents(&template_dir, &problem_dir)?;

        Ok(())
    }
}
```

### 3. 設定アクセスの整理

```rust
impl Contest {
    /// 言語固有の設定を取得
    fn get_language_config<T: TypedValue>(&self, config_path: &str) -> Result<T> {
        let language = self.language.as_ref()
            .ok_or_else(|| ContestError::Language("言語が設定されていません".into()))?;

        self.config.get::<T>(&format!("languages.{}.{}", language, config_path))
            .or_else(|_| self.config.get::<T>(config_path))
            .map_err(|e| ContestError::Config(e.to_string()).into())
    }
}
```

## 期待される効果

1. 責務の明確化
   - Config: 設定値の取得と解決
   - Contest: コンテスト固有の状態と操作

2. エラーハンドリングの改善
   - 設定エラーの明確化
   - エラーメッセージの一貫性

3. コードの整理
   - 重複コードの削減
   - パス解決ロジックの統一
   - テスト容易性の向上

## 作業手順

1. パス解決の整理
   - `get_test_dir`の実装
   - `get_problem_file_path`の修正

2. テンプレート関連の整理
   - `create_problem_directory`の修正
   - パス生成ロジックの統一

3. 設定アクセスの整理
   - `get_language_config`の修正
   - エラーハンドリングの統一 