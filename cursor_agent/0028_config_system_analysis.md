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

## 6. 既存の設定ファイル分析

### 6.1 Docker関連の設定構造
```yaml
docker:
  timeout_seconds: ${CPH_DOCKER_TIMEOUT-10}
  memory_limit_mb: ${CPH_DOCKER_MEMORY-256}
  mount_point: "/compile"
```

### 6.2 言語固有のDocker設定
```yaml
languages:
  rust:
    runner:
      image: "${CPH_RUST_IMAGE-rust:latest}"
      compile: ["rustc", "main.rs"]
      run: ["./main"]
      require_files: ["Cargo.toml"]
      env_vars:
        - "RUST_BACKTRACE=1"
```

### 6.3 環境変数による設定カスタマイズ
- `CPH_DOCKER_TIMEOUT`: タイムアウト時間
- `CPH_DOCKER_MEMORY`: メモリ制限
- `CPH_RUST_IMAGE`: Rustコンテナイメージ
- その他言語固有の環境変数

### 6.4 設定の再利用
- アンカー（`&lang_base`）を使用した設定の継承
- 言語間での共通設定の再利用
- オーバーライド可能なデフォルト値の提供

## 7. 結論

現状の設定ファイルは、Docker関連の機能を十分にカバーしており、以下の利点があります：

1. **柔軟な設定構造**
   - 言語ごとの個別設定
   - 共通設定の継承
   - 環境変数によるカスタマイズ

2. **運用性**
   - デフォルト値の提供
   - 環境変数による上書き
   - 設定の再利用性

3. **拡張性**
   - 新しい言語の追加が容易
   - Docker設定のカスタマイズが容易
   - 言語固有の要件に対応可能

提案された設定システムの改善は、この既存の設定構造を活かしつつ、型安全性と保守性を向上させることが可能です。 