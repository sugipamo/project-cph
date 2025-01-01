# Contest構造体のDefault実装削除

## 概要
- `Contest`構造体の`Default`実装を削除
- 代わりに目的特化型の`for_site_auth`メソッドを追加
- `login`コマンドの実装を修正

## 変更理由
1. 現状の`Default`実装は`login`コマンドでのみ使用
2. `Default`実装が持つ設定読み込みなどの機能は実際には使用されていない
3. より明確な初期化パターンを提供することで、コードの意図を明確化

## 具体的な変更
1. `Contest`構造体から`Default`実装を削除
2. 新しい`for_site_auth`メソッドを追加：
```rust
impl Contest {
    /// サイト認証用のコンテストインスタンスを作成
    pub fn for_site_auth(config: &Config) -> Result<Self> {
        Ok(Self {
            active_contest_dir: PathBuf::new(),
            contest_id: String::new(),
            language: None,
            site_id: String::new(),
            workspace_dir: std::env::current_dir()?,
            config: config.clone(),
        })
    }
}
```

3. `login`コマンドの修正：
```rust
async fn execute(&self, _command: &Commands, site_id: &str) -> Result<()> {
    let config = Config::load()?;
    let mut contest = Contest::for_site_auth(&config)?;
    contest.set_site(site_id)?;

    let workspace_path = std::env::current_dir()?;
    let oj = OJContainer::new(workspace_path, contest)?;
    oj.login().await?;

    Ok(())
}
```

## 期待される効果
1. コードの意図がより明確に
2. 不要な設定読み込みの削除
3. エラーハンドリングの改善

## 影響範囲
- `src/contest/mod.rs`: `Default`実装の削除、`for_site_auth`メソッドの追加
- `src/cli/commands/login.rs`: `Contest`インスタンス生成方法の変更

## 作業難易度
低: 削除と単純な追加のみ 