 # エイリアス実装の再設計計画

## 🎯 設計方針

### 1. シンプルな責任分離
1. **エイリアス解決**
   - 単純な文字列変換として実装
   - 大文字小文字の正規化を含む
   - コンテキストに依存しない設計

2. **コマンドパーサー**
   - エイリアス解決とは独立して実装
   - 引数の検証と変換を担当
   - エラーハンドリングの一元管理

3. **バリデーション**
   - 独立したモジュールとして実装
   - 各種IDや引数の検証を集中管理
   - カスタムエラー型の定義

## 📋 実装計画

### フェーズ1: 基本構造の実装（0.5h）
1. **新しいモジュール構造**
   ```rust
   src/config/
   ├── aliases.rs      # エイリアス解決の基本実装
   ├── parser.rs       # コマンドパーサー
   ├── validator.rs    # バリデーションロジック
   └── error.rs        # エラー型定義
   ```

2. **基本的なトレイトと型の定義**
   - `Resolver` トレイト: エイリアス解決の基本動作
   - `Parser` トレイト: コマンド解析の基本動作
   - `Validator` トレイト: バリデーションの基本動作

### フェーズ2: コア機能の実装（1h）
1. **エイリアス解決**
   ```rust
   impl AliasResolver {
       fn resolve(&self, input: &str) -> Option<String>
       fn normalize(&self, input: &str) -> String
   }
   ```

2. **コマンドパーサー**
   ```rust
   impl CommandParser {
       fn parse(&self, args: Vec<String>) -> Result<Command>
       fn validate(&self, cmd: &Command) -> Result<()>
   }
   ```

3. **バリデーション**
   ```rust
   impl Validator {
       fn validate_problem_id(&self, id: &str) -> Result<()>
       fn validate_language(&self, lang: &str) -> Result<()>
   }
   ```

### フェーズ3: テストの実装（1h）
1. **ユニットテスト**
   - エイリアス解決のテスト
   - コマンドパーサーのテスト
   - バリデーションのテスト

2. **統合テスト**
   - エッジケースのテスト
   - エラーケースのテスト

### フェーズ4: エラーハンドリングの実装（0.5h）
1. **エラー型の定義**
   ```rust
   #[derive(Error, Debug)]
   pub enum ConfigError {
       #[error("Invalid alias: {0}")]
       InvalidAlias(String),
       #[error("Invalid command: {0}")]
       InvalidCommand(String),
       #[error("Validation error: {0}")]
       ValidationError(String),
   }
   ```

## 🔍 テスト計画

### 1. エイリアス解決テスト
- 基本的な解決テスト
- 大文字小文字の正規化テスト
- 存在しないエイリアスのテスト

### 2. コマンドパーサーテスト
- 基本的なコマンド解析テスト
- 引数の解析テスト
- エラーケースのテスト

### 3. バリデーションテスト
- 問題IDのバリデーション
- 言語指定のバリデーション
- 特殊文字のハンドリング

## ⚠️ 注意点

1. **後方互換性**
   - 既存のYAML設定ファイルとの互換性維持
   - 既存のCLIインターフェースとの互換性維持

2. **エラーメッセージ**
   - ユーザーフレンドリーなエラーメッセージ
   - デバッグ情報の適切な提供

3. **パフォーマンス**
   - 不要なメモリ割り当ての回避
   - 効率的な文字列処理

## 📅 タイムライン

1. フェーズ1: 30分
2. フェーズ2: 1時間
3. フェーズ3: 1時間
4. フェーズ4: 30分

**合計予定時間: 3時間**