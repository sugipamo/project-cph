# 設定システム分析レポート

## 1. 現状の設定システム

### 1.1 基本機能
- `src/config/mod.rs`で提供される設定読み込み機能
- YAML形式の設定ファイルサポート
- 型安全な値の取得
- エイリアス解決機能
- 環境変数展開サポート

### 1.2 主要な型と構造体
```rust
pub struct Config {
    data: Value,
    alias_map: HashMap<String, String>,
    alias_sections: Vec<AliasSection>,
    anchor_prefix: String,
    required_values: Vec<RequiredValue>,
}

pub enum ConfigType {
    String,
    Integer,
    Float,
    Boolean,
    StringArray,
}

pub struct RequiredValue {
    pub path: String,
    pub description: String,
    pub config_type: ConfigType,
}
```

## 2. Docker設定との統合

### 2.1 現在のDocker設定
```rust
pub struct DockerConfig {
    pub timeout_seconds: u64,
    pub memory_limit_mb: u64,
    pub mount_point: String,
}

pub struct CompileConfig {
    pub extension: String,
    pub require_files: Vec<String>,
    pub env_vars: Vec<String>,
}
```

### 2.2 提案される改善点

#### DockerConfigの統合
```rust
impl DockerConfig {
    pub fn from_config(config: &Config) -> Result<Self, ConfigError> {
        Ok(Self::new(
            config.get("system.docker.timeout_seconds")?,
            config.get("system.docker.memory_limit_mb")?,
            config.get("system.docker.mount_point")?,
        ))
    }
}
```

#### 言語設定の統合
```rust
impl CompileConfig {
    pub fn from_config(config: &Config, lang: &str) -> Result<Self, ConfigError> {
        let resolved_lang = config.get_with_alias::<String>(&format!("{}.name", lang))?;
        Ok(Self::new(
            config.get(&format!("{}.extension", resolved_lang))?,
            config.get(&format!("{}.required_files", resolved_lang))?,
            config.get(&format!("{}.env_vars", resolved_lang))?,
        ))
    }
}
```

#### 必須値の検証追加
```rust
let config_builder = Config::builder()
    .add_required_value(
        "system.docker.timeout_seconds",
        "実行タイムアウト時間",
        ConfigType::Integer
    )
    .add_required_value(
        "system.docker.memory_limit_mb",
        "メモリ制限",
        ConfigType::Integer
    )
    .add_required_value(
        "system.docker.mount_point",
        "マウントポイント",
        ConfigType::String
    );
```

## 3. 実装の難易度

### 🟢 低い（1-2日）
- 既存の設定値の追加/変更
- 環境変数の追加
- 基本的な型の追加

### 🟡 中程度（3-5日）
- 新しい言語サポートの追加
- コンパイル設定の拡張
- エラーハンドリングの統一

### 🔴 高い（1週間以上）
- 設定スキーマの大規模な変更
- 複数コンテナ間の設定共有
- 動的な設定変更の実装

## 4. メリット

1. **型安全性の向上**
   - コンパイル時の型チェック
   - 設定値の型変換エラーの早期検出

2. **保守性の向上**
   - 統一された設定アクセス方法
   - 集中化された設定管理
   - 明確なエラーメッセージ

3. **拡張性**
   - 新しい設定項目の追加が容易
   - カスタム型のサポート
   - エイリアスによる柔軟な設定参照

4. **環境変数サポート**
   - 開発/本番環境での柔軟な設定変更
   - セキュアな機密情報の管理

## 5. 推奨される次のステップ

1. **既存の設定ファイルの移行**
   - 現在のDocker設定をYAML形式に変換
   - 必須値の定義を追加

2. **インターフェースの統一**
   - Docker関連の設定読み込みを`Config`構造体に統合
   - エラーハンドリングの統一

3. **テストの追加**
   - 設定読み込みのユニットテスト
   - エラーケースのテスト
   - 統合テストの追加

4. **ドキュメントの更新**
   - 設定ファイルのスキーマ定義
   - 使用例の追加
   - エラーメッセージの日本語化 