# FileManagerの実装における懸念点

## 1. バックアップの粒度

### 1.1 現状の課題
- 現在はディレクトリ単位でのバックアップのみ
- 個別ファイルの変更履歴が取れない
- 複数の変更を一括でロールバックする必要がある

### 1.2 改善案
```rust
pub struct FileManager {
    backup_dir: TempDir,
    // 変更履歴を保持
    changes: Vec<FileChange>,
    current_state: PathBuf,
}

struct FileChange {
    path: PathBuf,
    operation_type: OperationType,
    timestamp: DateTime<Utc>,
}

enum OperationType {
    Create,
    Modify,
    Delete,
    Move(PathBuf), // 移動先のパス
}
```

## 2. エラーハンドリング

### 2.1 現状の課題
- エラー型が単純な`String`
- エラーの種類による分岐処理が困難
- ロールバック時のエラーハンドリングが不十分

### 2.2 改善案
```rust
#[derive(Debug)]
pub enum FileManagerError {
    BackupError { source: std::io::Error, path: PathBuf },
    RollbackError { source: std::io::Error, path: PathBuf },
    CleanupError { source: std::io::Error },
    ValidationError { message: String },
}

type Result<T> = std::result::Result<T, FileManagerError>;
```

## 3. 並行処理への対応

### 3.1 現状の課題
- 複数のコマンドが同時に実行された場合の考慮がない
- ファイルロックの仕組みがない
- 競合状態の検出と解決ができない

### 3.2 改善案
```rust
use std::sync::{Arc, Mutex};

pub struct FileManager {
    backup_dir: TempDir,
    current_state: PathBuf,
    lock: Arc<Mutex<()>>,
}
```

## 4. テスト容易性

### 4.1 現状の課題
- 実際のファイルシステムに依存したテスト
- 複雑なシナリオのテストが困難
- モック化が難しい

### 4.2 改善案
```rust
pub trait FileSystem {
    fn copy(&self, from: &Path, to: &Path) -> Result<()>;
    fn remove(&self, path: &Path) -> Result<()>;
    fn exists(&self, path: &Path) -> bool;
}

pub struct FileManager<FS: FileSystem> {
    backup_dir: TempDir,
    current_state: PathBuf,
    fs: FS,
}
```

## 5. 設定変更の追跡

### 5.1 現状の課題
- 設定変更とファイル操作の関連付けができない
- 部分的なロールバックができない
- 変更の意図が記録されない

### 5.2 改善案
```rust
pub struct ChangeSet {
    id: String,
    description: String,
    changes: Vec<FileChange>,
    config_changes: Vec<ConfigChange>,
}

impl FileManager {
    pub fn create_change_set(&mut self, description: &str) -> ChangeSet {
        // 変更セットを作成
    }

    pub fn commit_change_set(&mut self, change_set: ChangeSet) -> Result<()> {
        // 変更を適用
    }

    pub fn rollback_change_set(&mut self, change_set_id: &str) -> Result<()> {
        // 特定の変更セットをロールバック
    }
}
```

## 6. 推奨される対応

1. **段階的な改善**:
   - まず基本機能を実装
   - 必要に応じて機能を追加
   - テストカバレッジを維持

2. **優先順位**:
   1. エラーハンドリングの改善
   2. 変更の追跡機能
   3. テスト容易性の向上
   4. 並行処理対応（必要な場合）

3. **設計原則**:
   - インターフェースの安定性を重視
   - 拡張性を確保
   - テストしやすい構造を維持 