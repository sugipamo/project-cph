# OJモジュールリファクタリング計画

## 現状の問題点
1. `OJContainer`が`Contest`構造体に強く依存している
2. 必要な情報（site, url等）を`Contest`経由で間接的に取得している
3. 設定ファイルへのアクセスが分散している

## 改善案

### 1. 新しいインターフェース
```rust
pub struct OJSite {
    pub name: String,
    pub url: String,
    pub problem_url_template: String,
}

pub struct OJContainer {
    workspace_path: PathBuf,
    site: OJSite,
    config: Config,
}
```

### 2. コンストラクタの改善
```rust
impl OJContainer {
    pub fn new(workspace_path: PathBuf, site_name: &str) -> Result<Self> {
        let config = Config::load()?;
        let site = Self::load_site_config(&config, site_name)?;
        Ok(Self { workspace_path, site, config })
    }

    fn load_site_config(config: &Config, site_name: &str) -> Result<OJSite> {
        Ok(OJSite {
            name: config.get(&format!("sites.{}.name", site_name))?,
            url: config.get(&format!("sites.{}.url", site_name))?,
            problem_url_template: config.get(&format!("sites.{}.problem_url", site_name))?,
        })
    }
}
```

### 3. メソッドの改善点
- `login`メソッド: `Contest`への依存を削除し、`site`フィールドを直接使用
- `open`メソッド: 問題URLを直接受け取るように変更
- `submit`メソッド: 変更なし（すでに問題情報を直接受け取っている）

## 期待される効果
1. 責任の分離: OJ関連の処理が`Contest`から独立
2. 明示的なデータフロー: 必要な情報を直接扱う
3. テスタビリティの向上: `Contest`なしでテスト可能

## 実装手順
1. `OJSite`構造体の追加
2. `OJContainer`の改修
3. 既存の呼び出し箇所の更新
4. テストの追加/更新 