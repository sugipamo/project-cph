# Contest構造体のConfig依存整理

## 現状の課題

1. 設定パスの散在
   - 同じ設定パスが複数のメソッドで重複して使用
   - パス文字列のハードコーディング
   - エラーメッセージの不統一

2. エラーハンドリングの重複
   - 同様のエラー変換処理が多数存在
   - エラーメッセージの生成パターンが統一されていない

3. 設定アクセスパターンの不統一
   - 直接`config.get`を使用する箇所
   - `get_language_config`を使用する箇所
   - エイリアス解決を行う箇所と行わない箇所

## 改善方針

### 1. 設定パスの定数化

```rust
impl Contest {
    // システム設定パス
    const PATH_ACTIVE_DIR: &'static str = "system.contest_dir.active";
    const PATH_STORAGE_DIR: &'static str = "system.contest_dir.storage";
    const PATH_TEMPLATE_DIR: &'static str = "system.contest_dir.template";
    const PATH_TEMPLATE_PATTERN: &'static str = "system.templates.directory";
    const PATH_TEST_DIR: &'static str = "system.test.dir";
    const PATH_CONTEST_CONFIG: &'static str = "system.active_contest_yaml";

    // 言語設定パス
    const PATH_DEFAULT_LANGUAGE: &'static str = "languages.default";
    const PATH_LANGUAGE_EXTENSION: &'static str = "languages.{}.extension";

    // サイト設定パス
    const PATH_SITE_URL: &'static str = "sites.{}.url";
    const PATH_SITE_PROBLEM_URL: &'static str = "sites.{}.problem_url";
    const PATH_SITE_SUBMIT_URL: &'static str = "sites.{}.submit_url";
}
```

### 2. 設定取得メソッドの整理

```rust
impl Contest {
    /// システム設定を取得
    fn get_system_config<T: TypedValue>(&self, path: &str) -> Result<T> {
        self.config.get(path)
            .map_err(|e| ContestError::Config(format!("システム設定の取得に失敗: {}", e)))
    }

    /// 言語設定を取得
    fn get_language_config<T: TypedValue>(&self, path: &str) -> Result<T> {
        let language = self.get_current_language()?;
        let full_path = path.replace("{}", &language);
        
        self.config.get(&full_path)
            .map_err(|e| ContestError::Language(format!("言語設定の取得に失敗: {}", e)))
    }

    /// サイト設定を取得
    fn get_site_config<T: TypedValue>(&self, path: &str) -> Result<T> {
        let full_path = path.replace("{}", &self.site_id);
        
        self.config.get(&full_path)
            .map_err(|e| ContestError::Site(format!("サイト設定の取得に失敗: {}", e)))
    }
}
```

### 3. エラーメッセージの統一

```rust
impl ContestError {
    fn config(message: impl Into<String>) -> Self {
        ContestError::Config(message.into())
    }

    fn language(message: impl Into<String>) -> Self {
        ContestError::Language(message.into())
    }

    fn site(message: impl Into<String>) -> Self {
        ContestError::Site(message.into())
    }
}
```

## 期待される効果

1. コードの保守性向上
   - 設定パスの一元管理
   - エラーメッセージの統一
   - 重複コードの削減

2. 可読性の向上
   - 設定パスの意図が明確に
   - エラーメッセージの一貫性
   - メソッドの責務が明確に

3. 拡張性の向上
   - 新しい設定の追加が容易に
   - エラーハンドリングの統一的な拡張が可能

## 作業手順

1. 設定パスの定数定義
2. 設定取得メソッドの実装
3. 既存メソッドの修正
4. エラーメッセージの統一

## 作業難易度
中: 既存コードの修正が必要だが、機能的な変更は最小限 