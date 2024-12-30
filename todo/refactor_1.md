# Docker関連コードのリファクタリング計画

## 現状の課題
1. 設定構造体の重複（`RunnerConfig`と`DockerConfig`）
2. Docker関連の構造体が分散している
3. テストファイルの重複と分散
4. 環境変数設定の管理が不統一

## 改善計画

### Phase 1: 設定構造体の統合
```rust
// 現在
struct RunnerConfig { ... }
struct DockerConfig { ... }

// 統合後
struct DockerSettings {
    timeout_seconds: u64,
    memory_limit_mb: u64,
    mount_point: String,
}

impl DockerSettings {
    pub fn default() -> Self { ... }
    pub fn from_yaml(path: impl AsRef<Path>) -> std::io::Result<Self> { ... }
}
```

### Phase 2: Docker関連構造体の整理
```rust
struct DockerRunner {
    command: DockerCommand,
    config: DockerSettings,
    state: Arc<Mutex<RunnerState>>,
}

// コマンド実行に関する責務を明確化
impl DockerCommand {
    // イメージ管理
    async fn manage_image(&self) -> Result<(), String> { ... }
    
    // コンテナ管理
    async fn manage_container(&self) -> Result<(), String> { ... }
    
    // I/O管理
    async fn manage_io(&self) -> Result<(), String> { ... }
}
```

### Phase 3: 環境変数設定の統一
```yaml
# languages.yaml
languages:
  python:
    runner:
      env_vars:
        - PYTHONUNBUFFERED=1
        - PYTHONIOENCODING=utf-8
  rust:
    runner:
      env_vars: []
```

### Phase 4: テストの統合と整理
```rust
// tests/docker/mod.rs
mod common;  // 共通のセットアップ/クリーンアップロジック
mod settings;  // 設定関連のテスト
mod runner;  // ランナー関連のテスト
```

## 実装手順

1. **設定構造体の統合**
   - `DockerSettings`構造体の作成
   - 既存の設定読み込みロジックの移行
   - テストの更新

2. **Docker関連構造体の整理**
   - `DockerCommand`の責務の明確化
   - メソッドの再編成
   - エラーハンドリングの統一

3. **環境変数設定の統一**
   - 言語設定YAMLの更新
   - 環境変数読み込みロジックの実装
   - テストケースの追加

4. **テストの統合**
   - 共通ロジックの抽出
   - テストケースの整理
   - カバレッジの確認

## 期待される効果

1. **コードの保守性向上**
   - 重複コードの削除
   - 責務の明確化
   - エラーハンドリングの統一

2. **テストの改善**
   - テストケースの整理
   - カバレッジの向上
   - セットアップ/クリーンアップの簡素化

3. **拡張性の向上**
   - 新しい言語の追加が容易
   - 設定の変更が容易
   - テストの追加が容易

## 注意点

1. **後方互換性**
   - 既存のAPIは維持
   - 段階的な移行
   - 十分なテストカバレッジ

2. **エラーハンドリング**
   - エラーメッセージの統一
   - ログ出力の改善
   - デバッグ情報の充実

3. **パフォーマンス**
   - メモリ使用量の監視
   - 処理速度の維持
   - リソース使用の最適化 