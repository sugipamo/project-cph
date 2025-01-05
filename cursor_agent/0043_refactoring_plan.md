# リファクタリング計画

## 1. エラー処理の改善

### 1.1 エラー型の変換実装
- `ConfigError` -> `ContestError`の変換を実装
- エラーチェーンの実装による詳細なエラー情報の提供
- エラーメッセージの改善

### 1.2 エラーコンテキストの強化
- エラー発生箇所の情報追加
- エラー原因と解決策のヒントを提供
- ログレベルの導入

## 2. テストの改善

### 2.1 テストヘルパーの導入
```rust
// tests/helpers/fs.rs
pub struct FsTestContext {
    temp_dir: TempDir,
    base_path: PathBuf,
}

impl FsTestContext {
    pub fn new() -> anyhow::Result<Self> {
        let temp_dir = TempDir::new()?;
        let base_path = temp_dir.path().to_path_buf();
        Ok(Self { temp_dir, base_path })
    }

    pub fn create_test_file(&self, name: &str, content: &str) -> anyhow::Result<PathBuf> {
        let path = self.base_path.join(name);
        std::fs::write(&path, content)?;
        Ok(path)
    }
}
```

### 2.2 テストの同期化
- 非同期テストを同期テストに変換
- テストケースの整理
- テストカバレッジの向上

## 3. モジュール構造の改善

### 3.1 ファイルシステム操作の分離
```rust
// contest/fs/manager.rs
pub struct FsManager {
    transaction: FileTransaction,
    base_path: PathBuf,
}

impl FsManager {
    pub fn new(base_path: impl Into<PathBuf>) -> Result<Self> {
        Ok(Self {
            transaction: FileTransaction::new("fs_manager")?,
            base_path: base_path.into(),
        })
    }
}
```

### 3.2 コンテスト管理の整理
- コアロジックの分離
- インターフェースの統一
- 設定管理の改善

## 実装手順

1. エラー処理の改善（1-2日）
   - エラー型の変換実装
   - エラーコンテキストの強化
   - テストの追加

2. テストの改善（2-3日）
   - テストヘルパーの実装
   - テストの同期化
   - テストカバレッジの確認

3. モジュール構造の改善（3-4日）
   - ファイルシステム操作の分離
   - コンテスト管理の整理
   - 新構造のテスト

## リスク管理

1. エラー処理の改善
   - リスク: 既存のエラーハンドリングへの影響
   - 対策: 段階的な導入とテストの充実

2. テストの改善
   - リスク: テストカバレッジの一時的な低下
   - 対策: 新旧テストの並行運用

3. モジュール構造の改善
   - リスク: 既存機能への影響
   - 対策: 機能単位での段階的な移行

## まとめ

このリファクタリング計画は、コードベースの品質と保守性を向上させることを目的としています。
各フェーズは独立して進めることができ、段階的な改善が可能です。
特にエラー処理とテストの改善から着手することで、安全にリファクタリングを進められると考えています。 