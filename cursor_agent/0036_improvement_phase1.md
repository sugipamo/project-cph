# フェーズ1改善計画：エラー処理とモジュール構造の整理

## 1. エラー型の再設計

### 実装手順
1. `ContestError`の再定義
```rust
#[derive(Error, Debug)]
pub enum ContestError {
    #[error("設定エラー: {message}")]
    Config { 
        message: String,
        source: Option<Box<dyn StdError + Send + Sync>>
    },

    #[error("ファイルシステムエラー: {message}, パス: {path:?}")]
    FileSystem {
        message: String,
        source: std::io::Error,
        path: PathBuf
    },

    #[error("検証エラー: {message}")]
    Validation {
        message: String
    },

    #[error("バックアップエラー: {message}, パス: {path:?}")]
    Backup {
        message: String,
        path: PathBuf,
        source: Option<Box<dyn StdError + Send + Sync>>
    }
}
```

2. エラー変換の実装
```rust
impl From<std::io::Error> for ContestError {
    fn from(err: std::io::Error) -> Self {
        ContestError::FileSystem {
            message: err.to_string(),
            source: err,
            path: PathBuf::new()
        }
    }
}
```

### 変更対象ファイル
- `src/contest/error.rs`
- `src/contest/file_manager.rs`
- `src/contest/mod.rs`

## 2. モジュール構造の整理

### ディレクトリ構造
```
src/contest/
├── error.rs          // エラー型の定義
├── file_manager/     // ファイル操作関連
│   ├── mod.rs
│   ├── backup.rs
│   └── operations.rs
├── test/             // テスト関連
│   ├── mod.rs
│   └── runner.rs
├── config/           // 設定管理
│   ├── mod.rs
│   └── validator.rs
└── mod.rs           // 公開インターフェース
```

### 実装手順
1. ディレクトリ構造の作成
2. 既存コードの移動
3. モジュール宣言の更新

## 3. ファイルマネージャーの改善

### 実装内容
```rust
pub struct FileManager {
    backup_manager: BackupManager,
    base_path: PathBuf,
}

impl FileManager {
    pub fn new(base_path: PathBuf) -> Result<Self, ContestError> {
        Ok(Self {
            backup_manager: BackupManager::new()?,
            base_path,
        })
    }

    pub fn create_directory(&self, path: &Path) -> Result<(), ContestError> {
        let full_path = self.base_path.join(path);
        self.backup_manager.backup(&full_path)?;
        
        if let Err(e) = fs::create_dir_all(&full_path) {
            self.backup_manager.restore()?;
            return Err(ContestError::FileSystem {
                message: "ディレクトリの作成に失敗".to_string(),
                source: e,
                path: full_path,
            });
        }
        Ok(())
    }

    // 他のファイル操作メソッドも同様に実装
}
```

## 4. テスト構造の改善

### テストユーティリティ
```rust
// src/contest/test/utils.rs
pub struct TestContext {
    pub temp_dir: TempDir,
    pub file_manager: FileManager,
}

impl TestContext {
    pub fn new() -> Result<Self, ContestError> {
        let temp_dir = TempDir::new()?;
        Ok(Self {
            file_manager: FileManager::new(temp_dir.path().to_path_buf())?,
            temp_dir,
        })
    }
}
```

### テストの実装
```rust
// src/contest/test/file_operations.rs
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_create_directory() -> Result<(), ContestError> {
        let ctx = TestContext::new()?;
        let test_dir = Path::new("test_dir");
        
        ctx.file_manager.create_directory(test_dir)?;
        assert!(ctx.temp_dir.path().join(test_dir).exists());
        Ok(())
    }
}
```

## 実装スケジュール

1. **Day 1: エラー型の再設計**
   - エラー型の実装
   - 変換関数の実装
   - 既存コードの更新

2. **Day 2: モジュール構造の整理**
   - ディレクトリ構造の作成
   - ファイルの移動
   - モジュール宣言の更新

3. **Day 3: ファイルマネージャーの改善**
   - 新しいファイルマネージャーの実装
   - バックアップ機能の統合
   - エラーハンドリングの改善

4. **Day 4: テスト構造の改善**
   - テストユーティリティの作成
   - テストケースの移行
   - テストの実行と検証

## 期待される効果

1. **エラー処理の改善**
   - より詳細なエラー情報
   - 一貫したエラーハンドリング
   - デバッグのしやすさ

2. **コードの整理**
   - 責務の明確な分離
   - メンテナンスの容易さ
   - 再利用性の向上

3. **テストの改善**
   - テストの構造化
   - テストの信頼性向上
   - カバレッジの向上

## 注意点

1. **後方互換性**
   - 公開APIの変更は最小限に
   - 既存の動作を維持

2. **段階的な移行**
   - 一度に大きな変更を避ける
   - 各ステップでテストを実行

3. **ドキュメント**
   - 変更内容の文書化
   - APIドキュメントの更新 