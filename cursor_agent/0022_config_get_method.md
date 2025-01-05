# Configの設定取得方法の修正

## 概要
- `Config`の設定取得方法を`get`メソッドの直接使用に変更
- 設定パスの構造を明示的に記述

## 変更理由
1. `Config`構造体は`get`メソッドのみを提供
2. 設定パスの構造を明示的にすることで可読性が向上
3. 型パラメータによる型安全性の確保

## 具体的な変更
1. システム設定の取得：
```rust
// 変更前
config.get_system("contest_dir.active")

// 変更後
config.get::<String>("system.contest_dir.active")
```

2. 言語設定の取得：
```rust
// 変更前
config.get_language(language, "extension")

// 変更後
config.get::<String>(&format!("languages.{}.extension", language))
```

3. サイト設定の取得：
```rust
// 変更前
config.get_site(site_id, "problem_url")

// 変更後
config.get::<String>(&format!("sites.{}.problem_url", site_id))
```

4. デフォルト言語の取得：
```rust
// 変更前
config.get_default_language()

// 変更後
config.get::<String>("languages.default")
```

## 期待される効果
1. `Config`構造体との整合性
2. 設定パスの明示的な表現
3. 型安全性の向上

## 影響範囲
- `src/contest/mod.rs`: 設定取得方法の修正

## 作業難易度
低: 単純な書き換え 