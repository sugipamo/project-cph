# 改善戦略

## フェーズ1: エラー処理の改善（1-2日）

### 1.1 エラー型の変換実装
```rust
// contest/error.rs に追加
impl From<ConfigError> for ContestError {
    fn from(err: ConfigError) -> Self {
        ContestError::Config {
            message: err.to_string(),
            source: Some(Box::new(err)),
        }
    }
}
```

### 1.2 エラーコンテキストの強化
- エラー発生箇所の情報追加
- エラーチェーンの実装
- ログレベルの導入

## フェーズ2: テストの改善（2-3日）

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

## フェーズ3: モジュール構造の改善（3-4日）

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

    pub fn create_directory(&mut self, path: impl AsRef<Path>) -> Result<()> {
        self.transaction.add_operation(CreateDirOperation::new(path));
        self.transaction.execute()
    }
}
```

### 3.2 コンテスト管理の整理
- コアロジックの分離
- インターフェースの統一
- 設定管理の改善

## 実装の優先順位

1. エラー処理の改善
   - 影響範囲が限定的
   - 即座に効果が得られる
   - 他の改善の基盤となる

2. テストの改善
   - 既存機能の安全性を確保
   - リファクタリングの支援
   - 品質の向上

3. モジュール構造の改善
   - 長期的な保守性の向上
   - 拡張性の確保
   - コードの整理

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

現状のコードベースは基本的な設計が健全であり、段階的な改善が可能です。
特にエラー処理とテストの改善から着手することで、安全に改善を進められると考えています。

各フェーズの改善は独立して進められるため、並行して作業を進めることも可能です。
また、各改善はそれぞれ独立したPRとして提出することで、レビューと統合を容易にします。 