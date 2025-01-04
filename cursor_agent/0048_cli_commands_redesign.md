# CLIコマンドの再設計

## 1. 現状の問題点

### 1.1 Contest構造体への強い依存
- 各コマンドが`Contest`構造体を直接使用
- 設定の読み込みと管理が各コマンドに分散
- テストやその他の機能が`Contest`に密結合

### 1.2 責務の混在
- コマンドの実行ロジックと状態管理が混在
- 設定の読み込みが各コマンドで重複
- エラー処理が不統一

## 2. 改善方針

### 2.1 引数ベースの設計
```rust
// Before
let mut contest = Contest::new(&config, &self.context.problem_id)?;
contest.run_test(&self.context.problem_id)?;

// After
pub async fn run_test(
    config: &Config,
    problem_id: &str,
    site_id: &str,
) -> Result<()> {
    let test_dir = get_test_dir(config, problem_id)?;
    run_test_cases(&test_dir)?;
    Ok(())
}
```

### 2.2 機能の分離
- テスト実行: `test::run_test`
- 言語設定: `language::set_language`
- 提出: `submit::submit_solution`
- 問題生成: `generate::generate_test`

### 2.3 設定の一元管理
```rust
pub struct ConfigContext {
    config: Config,
    site_id: String,
}

impl ConfigContext {
    pub fn new(site_id: impl Into<String>) -> Result<Self> {
        Ok(Self {
            config: Config::load()?,
            site_id: site_id.into(),
        })
    }
}
```

## 3. 実装計画

### 3.1 第1フェーズ: 基本機能の分離
1. テスト関連の機能を`test`モジュールに移動
2. 言語設定を`language`モジュールに移動
3. 提出機能を`submit`モジュールに移動
4. 生成機能を`generate`モジュールに移動

### 3.2 第2フェーズ: インターフェースの改善
1. 引数ベースのAPIに変更
2. エラー処理の統一
3. 設定管理の一元化

### 3.3 第3フェーズ: テストの追加
1. 各機能の単体テスト
2. 統合テスト
3. エラーケースのテスト

## 4. 修正手順

1. テスト関連
```rust
// src/test/mod.rs
pub async fn run_test(
    config: &Config,
    problem_id: &str,
    site_id: &str,
) -> Result<()> {
    let test_dir = get_test_dir(config, problem_id)?;
    run_test_cases(&test_dir)?;
    Ok(())
}
```

2. 言語設定
```rust
// src/language/mod.rs
pub fn set_language(
    config: &Config,
    problem_id: &str,
    language: &str,
) -> Result<()> {
    let solution_path = get_solution_path(config, problem_id)?;
    update_language_setting(config, problem_id, language)?;
    Ok(())
}
```

3. 提出機能
```rust
// src/submit/mod.rs
pub async fn submit_solution(
    config: &Config,
    problem_id: &str,
    site_id: &str,
) -> Result<()> {
    let solution_path = get_solution_path(config, problem_id)?;
    submit_to_site(config, site_id, problem_id, &solution_path)?;
    Ok(())
}
```

## 5. リスク管理

### 5.1 後方互換性
- 既存のテストが動作しなくなる可能性
- 一時的な機能の低下

### 5.2 移行戦略
1. 新しい実装を別モジュールとして追加
2. 段階的に既存コードを移行
3. テストでの検証を徹底

## まとめ

この再設計により：
1. `Contest`構造体への依存を排除
2. 機能ごとの責務を明確に分離
3. テストの容易性を向上
4. 保守性の向上

各機能を独立したモジュールとして実装し、引数ベースのインターフェースを提供することで、
より柔軟で保守しやすいコードベースを実現します。 