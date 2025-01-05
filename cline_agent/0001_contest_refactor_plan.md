# コンテストモジュールリファクタリング計画

## 現状の問題点

1. 責務の混在
   - Contest構造体が状態管理とバックアップ管理の両方を担当
   - 単一責任の原則に違反

2. 密結合
   - ContestStateとContest構造体が密結合
   - テストが困難

3. テストのメンテナンス性
   - Configのモック作成が手動
   - テストデータの構築が煩雑

## 改善案

### 1. 責務の分離

```rust
// 改善後の構造
ContestService
├── StateManager (ContestStateを管理)
└── BackupManager (バックアップを管理)
```

### 2. インターフェースの明確化

```rust
trait StateManager {
    fn get_state(&self) -> &ContestState;
    fn update_state(&mut self, state: ContestState);
}

trait BackupManager {
    fn create_backup(&self) -> Result<()>;
    fn restore_backup(&self) -> Result<()>;
}
```

### 3. テストの改善

- テスト用ビルダーを導入
- モック作成を簡素化

```rust
struct TestContestBuilder {
    state: ContestState,
    config: Config,
}

impl TestContestBuilder {
    fn new() -> Self {
        Self {
            state: ContestState::new(),
            config: Config::default(),
        }
    }

    fn with_problem(mut self, problem_id: &str) -> Self {
        self.state = self.state.with_problem(problem_id);
        self
    }

    fn build(self) -> ContestService {
        ContestService::new(self.state, self.config)
    }
}
```

## 実装手順

1. StateManagerトレイトの作成
2. BackupManagerトレイトの作成
3. ContestServiceの実装
4. テスト用ビルダーの実装
5. 既存コードの移行
6. テストのリファクタリング

## 期待される効果

- コードの複雑度低下
- テストの容易化
- 保守性の向上
- 拡張性の向上
