# コマンドパースと設定の統合アプローチ

## 同時解決すべき理由

1. **アーキテクチャの一貫性**
   - コマンドパースと設定は密接に関連
   - 両者の改善は相互に影響
   - 統一的なアプローチが必要

2. **共通の課題解決**
   - エラーハンドリング
   - バリデーション機構
   - 型安全性の確保

3. **開発効率**
   - 同時に改善することで重複作業を回避
   - 整合性のとれた設計が可能
   - テスト戦略の統一

## 統合アプローチ

### 1. 共通基盤の整備
```rust
// 共通のエラー型
pub enum AppError {
    ConfigError(ConfigError),
    ParseError(ParseError),
    ValidationError(ValidationError),
}

// 共通のバリデーション機構
trait Validator {
    fn validate(&self) -> Result<(), ValidationError>;
}
```

### 2. 設定とパースの統合
```rust
// 統合された設定管理
struct AppConfig {
    languages: LanguageConfig,
    sites: SiteConfig,
    commands: CommandConfig,
    // 他の設定...
}

// コマンドパーサーと設定の連携
struct CommandParser {
    config: Arc<AppConfig>,
    // パース関連のフィールド...
}
```

### 3. 実装の優先順位

1. **フェーズ1: 基盤整備**
   - 共通エラー型の定義
   - バリデーション機構の設計
   - 基本的な型の整理

2. **フェーズ2: 設定の統合**
   - 設定の階層化
   - 読み込み機構の統一
   - バリデーションの実装

3. **フェーズ3: パーサーの改善**
   - `clap`の`derive`機能活用
   - 設定との連携強化
   - エラーハンドリングの統合

4. **フェーズ4: テストと最適化**
   - 統合テストの実装
   - パフォーマンス最適化
   - エラーメッセージの改善

## 具体的な実装戦略

### 1. 共通モジュールの作成
```rust
// src/common/mod.rs
pub mod error;
pub mod validation;
pub mod config;
```

### 2. 設定の階層化
```rust
// src/config/mod.rs
pub struct AppConfig {
    inner: Arc<ConfigInner>,
}

struct ConfigInner {
    languages: LanguageConfig,
    sites: SiteConfig,
    commands: CommandConfig,
    validation: ValidationConfig,
}
```

### 3. パーサーの改善
```rust
// src/cli/parser.rs
pub struct Parser {
    config: Arc<AppConfig>,
}

impl Parser {
    pub fn new(config: Arc<AppConfig>) -> Self {
        Self { config }
    }

    pub fn parse(&self, args: Vec<String>) -> Result<Command, AppError> {
        // 設定を参照しながらパース
        // バリデーション
        // エラーハンドリング
    }
}
```

## 期待される効果

1. **保守性の向上**
   - 一貫した設計による理解容易性
   - 共通機能の再利用
   - 明確な責任分担

2. **信頼性の向上**
   - 統合されたエラーハンドリング
   - 包括的なバリデーション
   - 型安全性の確保

3. **拡張性の向上**
   - 新機能追加の容易さ
   - 設定変更の影響範囲の明確化
   - テスト容易性

## 注意点

1. **段階的な移行**
   - 既存機能を維持しながら改善
   - 各フェーズでの動作確認
   - ユーザー影響の最小化

2. **パフォーマンス考慮**
   - 設定読み込みの最適化
   - メモリ使用の効率化
   - 起動時間への影響

3. **エラーハンドリング**
   - ユーザーフレンドリーなメッセージ
   - デバッグ情報の提供
   - ログ機能の整備 