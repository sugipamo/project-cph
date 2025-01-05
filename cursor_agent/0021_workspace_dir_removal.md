# workspace_dirの削除

## 概要
- `workspace_dir`フィールドの削除
- パス解決ロジックの`active_contest_dir`への統合

## 変更理由
1. `workspace_dir`は`active_contest_dir`からの相対パスで代替可能
2. パス解決の責務を一箇所に集中させることでロジックが明確に
3. 不要なフィールドの削除によるコードの簡素化

## 具体的な変更
1. `Contest`構造体からの`workspace_dir`フィールドの削除：
```rust
pub struct Contest {
    pub active_contest_dir: PathBuf,
    pub contest_id: String,
    pub language: Option<String>,
    pub site_id: String,
    config: Config,
}
```

2. パス解決ロジックの修正：
```rust
impl Contest {
    fn get_template_dir(&self, language: &str) -> Result<PathBuf> {
        let template_pattern = self.config.get_system("templates.directory")?;
        let template_base = self.config.get_system("contest_dir.template")?;
        
        let template_dir_name = template_pattern.replace("{name}", language);
        Ok(self.active_contest_dir.parent().unwrap()
            .join(template_base)
            .join(template_dir_name))
    }

    fn get_contests_dir(&self) -> Result<PathBuf> {
        let storage_base = self.config.get_system("contest_dir.storage")?;
        Ok(self.active_contest_dir.parent().unwrap().join(storage_base))
    }
}
```

3. 初期化処理の修正：
```rust
impl Contest {
    pub fn new(config: &Config, problem_id: &str) -> Result<Self> {
        let active_dir = config.get_system("contest_dir.active")?;
        let active_contest_dir = std::env::current_dir()?.join(active_dir);

        // ...残りの初期化処理...
    }
}
```

## 期待される効果
1. コードの簡素化
2. パス解決ロジックの一元化
3. 責務の明確化

## 影響範囲
- `src/contest/mod.rs`: パス解決ロジックの修正
- `src/oj/mod.rs`: パス解決方法の変更

## 作業難易度
低: 単純なリファクタリング 