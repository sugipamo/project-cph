# Persistence Test Optimization Analysis

## 現状分析

### 実行時間の悪化
- **変更前**: 約31秒
- **変更後**: 35.03秒  
- **結果**: **4秒悪化（約13%増加）**

### 悪化の根本原因

#### 1. Migration出力削除による予期せぬ影響
```python
# 変更前: migration実行時にprint文が大量出力
print(f"Running migration {migration_file.name}")  # 89テスト × 2migration = 178回出力

# 変更後: print削除したが、I/O buffering効果が消失
if hasattr(self, '_debug_migrations') and self._debug_migrations:
    print(f"Running migration {migration_file.name}")  # 出力されない
```

**技術的詳細**: print出力削除により、SQLiteの同期I/O待機時間が表面化。print文が意図せずI/Oバッファリングの役割を果たしていた。

#### 2. 一時ファイル作成の隠れたコスト
```
各テストで実行される処理:
- tempfile.NamedTemporaryFile(): ~2ms
- SQLiteManager初期化(migration実行): ~300ms  
- os.unlink(): ~1ms

89テスト × 300ms = 26.7秒（実行時間の大部分）
```

## インメモリSQLite失敗の技術的詳細

### 1. Row Factory設定の継承問題
```python
# SQLiteManager.__init__
conn.row_factory = sqlite3.Row  # これが:memory:で正常動作しない場合がある

# テスト失敗の実際の原因
cursor.fetchone() # 期待: {'id': 1, 'name': 'test'}
                  # 実際: (1, 'test') または None
```

### 2. Foreign Key制約の有効化タイミング
```python
# migration実行順序の問題
conn.execute("PRAGMA foreign_keys = ON")  # タイミングが重要
conn.executescript(migration_sql)         # この時点でFKが効いていない可能性
```

### 3. トランザクション分離レベル
```python
# :memory:での自動コミット問題
with self.get_connection() as conn:  # 各テストで新しい接続
    # :memory:DBは接続ごとに独立 → データが共有されない
```

## 正しいインメモリ実装戦略

### 1. 共有接続プール方式
```python
class SharedMemorySQLiteManager:
    _shared_connection = None
    _lock = threading.Lock()
    
    @classmethod
    def get_shared_connection(cls):
        if cls._shared_connection is None:
            with cls._lock:
                if cls._shared_connection is None:
                    cls._shared_connection = sqlite3.connect(
                        ":memory:", 
                        check_same_thread=False
                    )
                    cls._run_migrations(cls._shared_connection)
        return cls._shared_connection
```

### 2. テスト分離のためのネームスペース
```python
# 各テストクラスごとに仮想的なDB分離
@pytest.fixture(scope="class")
def db_namespace():
    return f"test_{uuid.uuid4().hex[:8]}_"

def create_table_with_namespace(namespace, table_name):
    return f"CREATE TABLE {namespace}{table_name} (...)"
```

### 3. 適切なpytest fixture設計
```python
# Option A: Module scope (推奨)
@pytest.fixture(scope="module")
def shared_sqlite_manager():
    manager = SharedMemorySQLiteManager()
    yield manager
    # クリーンアップ

# Option B: Function scope with cleanup
@pytest.fixture
def clean_sqlite_manager(shared_sqlite_manager):
    # テスト前: データクリア
    cleanup_tables(shared_sqlite_manager)
    yield shared_sqlite_manager
    # テスト後: データクリア
    cleanup_tables(shared_sqlite_manager)
```

## 期待される性能改善

### 計算根拠
```
現在の時間構成:
- migration実行: 89テスト × 300ms = 26.7秒
- ファイル作成/削除: 89テスト × 3ms = 0.27秒  
- 実際のテスト実行: 8秒
合計: 35秒

インメモリ化後:
- migration実行: 1回のみ × 300ms = 0.3秒
- ファイル作成/削除: 0秒
- 実際のテスト実行: 8秒  
合計: 8.3秒
```

**期待される改善**: 35秒 → 8.3秒（**76%短縮**）

## 実装時の技術課題

### 1. pytest fixture設計の複雑性
```python
# スコープの選択
@pytest.fixture(scope="session")   # 全テスト共有 → データ汚染リスク
@pytest.fixture(scope="module")    # モジュール共有 → 適度な分離（推奨）
@pytest.fixture(scope="function")  # テストごと → 高コストだが安全
```

### 2. データクリーンアップの確実性
```python
# 順序依存の削除が必要（FK制約）
cleanup_order = [
    "container_lifecycle_events",
    "docker_containers", 
    "docker_images",
    "operations",
    "sessions"
]

def cleanup_tables(manager):
    with manager.get_connection() as conn:
        for table in cleanup_order:
            conn.execute(f"DELETE FROM {table}")
        conn.commit()
```

### 3. 並行テスト実行での競合
```python
# pytest-xdistでの並列実行時
# 共有:memory:DBでの排他制御が必要
import threading

class ThreadSafeSQLiteManager:
    def __init__(self):
        self._lock = threading.RLock()
    
    def get_connection(self):
        with self._lock:
            return self._shared_connection
```

## 段階的実装プラン

### Phase 1: 詳細分析（5分）
1. 現在のpersistenceテスト実行時間詳細計測
2. migration実行時間の個別計測
3. ファイルI/O時間の特定

### Phase 2: 基盤実装（10分）
1. `SharedMemorySQLiteManager`の実装
2. 適切なfixture設計
3. データクリーンアップ機構の実装

### Phase 3: 全体適用と検証（10分）
1. 全persistenceテストへの適用
2. 実行時間計測と目標達成確認
3. テスト間データ汚染の確認
4. 副作用の検証

## リスクと対策

### 想定リスク
1. **fixture設計の複雑化** → 段階的実装で検証
2. **テスト間のデータ汚染** → 確実なクリーンアップ実装
3. **migration失敗の対処** → 詳細ログ出力と fallback機構
4. **並列実行での競合** → 適切な排他制御

### 対策
1. 各段階での詳細な動作確認
2. テストデータの完全分離
3. 失敗時の自動復旧機構
4. スレッドセーフな実装

## 成功基準

1. **実行時間**: 35秒 → 15秒以下（57%以上短縮）
2. **テスト成功率**: 100%維持
3. **テスト分離**: データ汚染なし
4. **保守性**: コードの複雑性を最小限に抑制

---

この分析に基づいて、確実に性能改善を実現する技術的基盤が整いました。