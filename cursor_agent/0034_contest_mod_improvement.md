# Contest モジュール 改善実装方針

## 概要
前回の分析で指摘された問題点を踏まえ、以下の実装方針を提案します。

## 1. モジュール構造の再設計

```rust
src/contest/
├── mod.rs                 // 公開インターフェース
├── core/                  // コアロジック
│   ├── mod.rs
│   ├── contest.rs         // コンテスト基本情報
│   └── state.rs          // 状態管理
├── fs/                    // ファイルシステム
│   ├── mod.rs
│   ├── manager.rs        // ファイル操作
│   └── backup.rs         // バックアップ
├── test/                  // テスト関連
│   ├── mod.rs
│   ├── runner.rs         // テストランナー
│   └── generator.rs      // テストケース生成
└── online_judge/         // オンラインジャッジ
    ├── mod.rs
    ├── client.rs         // API通信
    └── auth.rs           // 認証
```

## 2. 責務の分離

### Contest構造体の簡素化
```rust
pub struct Contest {
    state: ContestState,
    config: Arc<Config>,
    fs_manager: Arc<FileSystemManager>,
    test_manager: Arc<TestManager>,
    oj_client: Arc<OnlineJudgeClient>,
}
```

### 各マネージャーの実装
```rust
// ファイルシステム管理
pub struct FileSystemManager {
    backup_manager: BackupManager,
    path_validator: PathValidator,
}

// テスト管理
pub struct TestManager {
    runners: HashMap<String, Box<dyn TestRunner>>,
    generator: TestGenerator,
}

// オンラインジャッジクライアント
pub struct OnlineJudgeClient {
    auth_manager: AuthManager,
    api_client: ApiClient,
}
```

## 3. エラー処理の改善

### エラー型の階層化
```rust
#[derive(Error, Debug)]
pub enum ContestError {
    #[error("ファイルシステムエラー: {0}")]
    FileSystem(#[from] FileSystemError),
    
    #[error("設定エラー: {0}")]
    Config(#[from] ConfigError),
    
    #[error("オンラインジャッジエラー: {0}")]
    OnlineJudge(#[from] OnlineJudgeError),
    
    #[error("検証エラー: {0}")]
    Validation(#[from] ValidationError),
}
```

### コンテキスト情報の追加
```rust
pub struct ErrorContext {
    operation: String,
    location: String,
    timestamp: DateTime<Utc>,
    details: HashMap<String, String>,
}
```

## 4. 設定管理の改善

### 動的設定管理
```rust
pub struct DynamicConfig {
    inner: Arc<RwLock<Config>>,
    validator: ConfigValidator,
    watcher: ConfigWatcher,
}
```

### スキーマ検証
```rust
pub struct ConfigValidator {
    schema: ConfigSchema,
    constraints: Vec<Box<dyn ConfigConstraint>>,
}
```

## 5. テスト機能の抽象化

### テストランナーインターフェース
```rust
#[async_trait]
pub trait TestRunner: Send + Sync {
    async fn compile(&self, source: &Path) -> Result<()>;
    async fn run_test(&self, input: &str) -> Result<String>;
    async fn validate(&self, output: &str, expected: &str) -> Result<bool>;
}
```

### 言語別実装
```rust
pub struct RustTestRunner {
    compiler: RustCompiler,
    executor: TestExecutor,
}

pub struct PythonTestRunner {
    interpreter: PythonInterpreter,
    executor: TestExecutor,
}
```

## 6. ファイル操作の安全性向上

### トランザクション的操作
```rust
pub struct FileTransaction {
    operations: Vec<FileOperation>,
    backup: BackupManager,
}

impl FileTransaction {
    pub async fn execute(self) -> Result<()> {
        self.backup.create().await?;
        for op in self.operations {
            if let Err(e) = op.execute().await {
                self.backup.restore().await?;
                return Err(e);
            }
        }
        self.backup.commit().await
    }
}
```

## 7. メモリ効率の改善

### ストリーム処理の導入
```rust
pub trait FileProcessor {
    type Item;
    
    fn process_stream<R: AsyncRead>(
        &self,
        reader: R,
    ) -> Pin<Box<dyn Stream<Item = Result<Self::Item>>>>;
}
```

## 実装スケジュール

1. フェーズ1: 基本構造の再設計
   - モジュール構造の整理
   - 基本インターフェースの定義
   - エラー型の再設計

2. フェーズ2: コア機能の実装
   - ファイルシステム管理
   - テスト実行機能
   - 設定管理

3. フェーズ3: 拡張機能の実装
   - オンラインジャッジ連携
   - 高度なテスト機能
   - パフォーマンス最適化

## まとめ

この実装方針により、以下の改善が期待できます：

1. コードの保守性向上
2. 機能の独立性確保
3. エラー処理の堅牢化
4. テスト容易性の向上
5. パフォーマンスの改善
6. 拡張性の確保

各コンポーネントが明確な責務を持ち、適切に分離されることで、長期的な保守性と拡張性が確保されます。 