# 設定ファイルのバリデーション強化

## 現状の問題点

1. 必須設定値の検証が不十分
   - `languages.default`が未設定の場合のエラーメッセージが不明確
   - 設定値の存在チェックが個別の箇所で行われている
   - エラーメッセージが統一されていない

2. エラーハンドリングの課題
   - `ConfigError::RequiredValueError`が存在するが、十分に活用されていない
   - エラーメッセージが英語と日本語が混在している
   - エラーの文脈情報が不足している

## 改善案

### 1. 必須設定値の検証機能の追加

```rust
impl Config {
    // 必須設定値を検証するメソッドを追加
    pub fn validate_required_values(&self) -> Result<(), ConfigError> {
        // 必須設定値のリスト
        let required_values = vec![
            ("languages.default", "デフォルト言語"),
            ("system.browser", "ブラウザ設定"),
            ("system.docker.timeout_seconds", "Dockerタイムアウト"),
            // 他の必須設定値を追加
        ];

        for (path, description) in required_values {
            if let Err(ConfigError::PathError(_)) = self.get_raw(path) {
                return Err(ConfigError::RequiredValueError(
                    format!("必須設定 '{}' ({}) が設定されていません", path, description)
                ));
            }
        }
        Ok(())
    }
}
```

### 2. エラーメッセージの改善

```rust
impl std::fmt::Display for ConfigError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            ConfigError::RequiredValueError(msg) => write!(f, "設定エラー: {}", msg),
            ConfigError::PathError(path) => write!(f, "設定エラー: パス '{}' が見つかりません", path),
            // 他のエラーケース
        }
    }
}
```

### 3. 設定読み込み時の自動検証

```rust
impl Config {
    pub fn from_file(path: &str, builder: ConfigBuilder) -> Result<Self, ConfigError> {
        let mut config = Self::load_from_file(path, builder)?;
        config.validate_required_values()?;  // 必須設定値を検証
        Ok(config)
    }
}
```

## 実装の優先度

### 優先度：高
1. 必須設定値の検証機能の実装
   - `validate_required_values`メソッドの追加
   - 主要な必須設定値の定義

### 優先度：中
1. エラーメッセージの統一
   - 日本語エラーメッセージへの統一
   - より詳細な文脈情報の提供

### 優先度：低
1. 設定値の型検証の強化
   - 値の型チェックの追加
   - カスタムバリデーションルールの追加

## 影響範囲

1. 設定ファイルの読み込み処理
   - `src/config/mod.rs`
   - `src/contest/mod.rs`

2. エラーハンドリング
   - 各コマンドの実装
   - テストケース

## テスト項目

1. 必須設定値の検証
   - 設定が存在する場合
   - 設定が存在しない場合
   - 設定値が不正な場合

2. エラーメッセージ
   - メッセージの一貫性
   - 文脈情報の正確性

3. 設定ファイルの読み込み
   - 正常系のテスト
   - 異常系のテスト 