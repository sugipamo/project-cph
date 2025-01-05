# Contest構造体の設定読み込み改善

## 現状の問題
1. `Contest`構造体の各メソッドで`Config::load()`を個別に呼び出している
2. 引数として渡された`config`が無視され、不必要な設定の再読み込みが発生
3. パフォーマンスとリソースの無駄遣いが発生

## 影響を受けているメソッド
1. `impl Default for Contest`
2. `Contest::new`
3. `Contest::save`
4. `Contest::get_solution_language`
5. `Contest::set_language`
6. `Contest::set_site`
7. `Contest::move_files_to_contests`
8. `Contest::read_moveignore`
9. `Contest::create_problem_directory`

## 修正方針
1. `Contest`構造体に`config: Config`フィールドを追加
2. コンストラクタで渡された`Config`インスタンスを保持
3. 各メソッドで保持している`Config`インスタンスを使用

## 修正例
```rust
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Contest {
    #[serde(default)]
    pub active_contest_dir: PathBuf,
    pub contest_id: String,
    pub language: Option<String>,
    pub site: Site,
    #[serde(skip)]
    workspace_dir: PathBuf,
    #[serde(skip)]
    config: Config,  // 追加
}

impl Contest {
    pub fn new(config: &Config, problem_id: &str) -> Result<Self> {
        let active_dir = config.get::<String>("system.contest_dir.active")?;
        // ...
        Ok(Self {
            // ...
            config: config.clone(),
        })
    }

    // 他のメソッドでもself.configを使用
    pub fn save(&self) -> Result<()> {
        let config_file = self.config.get::<String>("system.active_contest_yaml")?;
        // ...
    }
}
```

## 作業難易度
🟡 中程度
- 構造体の変更と、それに伴う多くのメソッドの修正が必要
- シリアライズ/デシリアライズの処理の調整が必要

## 期待される効果
1. パフォーマンスの向上
   - 不必要な設定ファイルの読み込みを削減
   - メモリ使用量の削減

2. コードの品質向上
   - より明確な依存関係
   - 設定の一貫性の保証

3. 保守性の向上
   - 設定関連の変更が一箇所で管理可能
   - テストが容易に 