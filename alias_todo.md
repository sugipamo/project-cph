# エイリアス実装の再設計計画（最小実装版）

## 🎯 設計方針

### 1. コアコンポーネント
1. **Context管理**
   - コマンド実行コンテキストの管理
   - 状態遷移の基本制御
   - シンプルな設計を維持

2. **エイリアス解決**
   - 種類別の解決ロジック（言語、コマンド、サイト）
   - コンテキストベースの基本的な分岐処理
   - シンプルな文字列変換として実装

3. **バリデーション**
   - 必須チェックの実装
   - 基本的な引数検証
   - エラーの基本ハンドリング

## 📋 実装計画

### フェーズ1: 基盤整備（2h）
1. **モジュール構造**
   ```rust
   src/config/
   ├── context.rs     # コンテキスト管理（シンプル化）
   ├── aliases.rs     # 全エイリアス処理を1ファイルに集約
   ├── parser.rs      # コマンドパース
   └── validator.rs   # 基本バリデーション
   ```

2. **基本的な型定義**
   ```rust
   pub struct CommandContext {
       site: Site,
       mode: Mode,
       current_state: CommandState,
   }

   pub trait AliasResolver {
       fn resolve(&self, input: &str, context: &CommandContext) -> Option<String>;
   }
   ```

### フェーズ2: コア機能実装（3h）
1. **エイリアス解決の実装**
   ```rust
   impl AliasResolver {
       fn resolve_language(&self, input: &str) -> Option<String>
       fn resolve_command(&self, input: &str, context: &CommandContext) -> Option<String>
       fn resolve_site(&self, input: &str) -> Option<String>
   }
   ```

2. **バリデーションとパース**
   ```rust
   impl CommandParser {
       fn parse(&self, args: Vec<String>) -> Result<Command>
       fn validate_basic(&self, cmd: &Command) -> Result<()>
   }
   ```

### フェーズ3: 基本テスト（1h）
1. **必須テストケース**
   - 基本的なエイリアス解決のテスト
   - 主要なコマンドパターンのテスト
   - クリティカルなエラーケースのテスト

## ⚠️ 注意点

1. **優先度**
   - 基本機能の確実な動作を優先
   - エラーハンドリングは必要最小限に
   - テストは重要なケースのみに集中

2. **後回しにする機能**
   - 詳細なエラーメッセージ
   - エッジケースのテスト
   - 高度なバリデーションルール
   - 詳細なドキュメント作成