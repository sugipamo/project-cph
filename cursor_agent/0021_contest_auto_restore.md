# Contest構造体の自動復元機能の実装

## 概要
`Contest`構造体のインスタンス作成時に、`contests.yaml`から前回の設定を自動的に復元する機能を実装します。

## 現状の課題
1. `Contest::new`で新規作成時、`site_id`が空文字列で初期化される
2. 前回の設定（言語、サイト）が引き継がれない
3. 各コマンドで個別に設定を行う必要がある

## 修正方針

### 1. `contests.yaml`からの設定読み込み
```rust
impl Contest {
    pub fn new(config: &Config, problem_id: &str) -> Result<Self> {
        let config_file = config.get::<String>("system.active_contest_yaml")?;
        let config_path = active_contest_dir.join(&config_file);

        if config_path.exists() {
            // 既存の設定を読み込む
            let content = fs::read_to_string(&config_path)?;
            let mut contest: Contest = serde_yaml::from_str(&content)?;
            
            // 新しい問題用に更新
            contest.contest_id = contest_id;
            contest.config = config.clone();
            return Ok(contest);
        }

        // 新規作成時はデフォルト値で初期化
        let mut contest = Self {
            active_contest_dir,
            contest_id,
            language: None,
            site_id: String::new(),
            config: config.clone(),
        };

        // デフォルト言語を設定
        if let Ok(default_lang) = config.get::<String>("languages.default") {
            contest.language = Some(default_lang);
        }

        Ok(contest)
    }
}
```

### 2. 復元対象の設定
1. `site_id`: コンテストサイトの識別子
2. `language`: プログラミング言語の設定
3. その他の設定は必要に応じて追加

## 期待される効果
1. コマンド実行時の設定手順の簡略化
2. 一貫した設定の維持
3. ユーザー体験の向上

## 影響範囲
1. `src/contest/mod.rs`
   - `Contest::new`メソッドの修正
   - `Contest`構造体のシリアライズ設定

2. 各コマンドの実装
   - `work`コマンド: 初期設定の保存
   - その他のコマンド: 設定の自動復元を前提とした実装

## 作業難易度
低: 既存のコードを活用した単純な修正 