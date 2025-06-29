# 依存関係問題とCLAUDE.md違反の失敗パターン分析

## 概要
CPHプロジェクトの履歴ファイル分析から判明した、依存関係問題とCLAUDE.md違反の主要な失敗パターンを記載します。

## 1. デフォルト引数の多用パターン

### 1.1 発生状況
- **違反数**: 27ファイル、合計15個以上の関数
- **最も多い層**: Infrastructure層（12箇所）、Presentation層（8箇所）

### 1.2 典型的な失敗パターン
```python
# BAD: デフォルト値の使用
def execute(self, sql: str, parameters: Tuple = ()):  # 違反
    pass

def find_unused_images(self, days: int = 30):  # 違反
    pass

def main(argv: Optional[list[str]], exit_func, infrastructure, config_manager=None):  # 違反
    pass
```

### 1.3 根本原因
- **利便性の優先**: 開発者の利便性を優先した結果、CLAUDE.mdの規約を無視
- **段階的な蓄積**: 「一時的」として追加したデフォルト値が恒久化
- **テストの容易性**: デフォルト値があるとテストが書きやすいという短期的視点

### 1.4 影響
- テストカバレッジの偏り（デフォルト値の場合のみテストされる傾向）
- 暗黙的な動作による予期しないバグ
- 設定の硬直化

## 2. フォールバック処理（.get()、or演算子、try-except）

### 2.1 発生状況
- **違反箇所**: 最低8箇所以上
- **主な発生場所**: Configuration層、Runtime Config Overlay

### 2.2 典型的な失敗パターン
```python
# BAD: JSONデコード失敗時のフォールバック
try:
    configs[key] = json.loads(value)
except json.JSONDecodeError:
    configs[key] = value  # 違反：フォールバック処理

# BAD: キーが存在しない場合のフォールバック
try:
    return self._config[key]
except (KeyError, TypeError):
    return default_value  # 違反：デフォルト値へのフォールバック

# BAD: .get()によるフォールバック
config_value = config.get('key', 'default')  # 違反
```

### 2.3 根本原因
- **エラー処理の怠慢**: 適切なエラー処理の代わりにフォールバックで済ませる
- **設定の曖昧さ**: 必須設定とオプション設定の区別が不明確
- **互換性の言い訳**: 「既存コードとの互換性」を理由に違反を正当化

### 2.4 影響
- エラーの隠蔽により、問題の発見が遅れる
- 予期しない動作の原因となる
- デバッグの困難化

## 3. 副作用の不適切な配置（36箇所以上）

### 3.1 発生状況
- **違反数**: 36箇所以上
- **主な違反内容**:
  - Application層でのファイルI/O（3箇所）
  - Utils層でのsubprocess実行（2箇所）
  - Utils層でのOS操作（多数）
  - Configuration層でのJSON操作（多数）

### 3.2 典型的な失敗パターン
```python
# BAD: Application層での直接ファイル読み込み
class SqliteManager:
    def load_migration(self, path):
        with open(path, 'r') as f:  # 違反：infrastructure層以外での副作用
            return f.read()

# BAD: Utils層でのsubprocess実行
def run_command(cmd):
    return subprocess.run(cmd, shell=True)  # 違反：infrastructure層以外での副作用

# BAD: Utils層でのOS操作
def normalize_path(path):
    return os.path.normpath(path)  # 違反：infrastructure層以外での副作用
```

### 3.3 根本原因
- **レイヤー責務の誤解**: 各層の責任範囲が不明確
- **便宜的な実装**: 「動けばよい」という短期的思考
- **依存性注入の不徹底**: インフラストラクチャの抽象化が不完全

### 3.4 影響
- テストの困難化（モックが必要な箇所が多すぎる）
- 層の結合度が高くなり、変更が困難
- 副作用の管理が分散し、把握が困難

## 4. テストカバレッジの偏り

### 4.1 発生状況
- **0%カバレッジ**: 14ファイル（主にutils層）
- **60%未満**: 7ファイル
- **60-75%**: 約20ファイル

### 4.2 典型的な失敗パターン
```
# カバレッジが低い/ゼロのモジュール
src/utils/docker_path_ops.py: 0%
src/utils/path_operations.py: 0%
src/utils/retry_decorator.py: 0%
src/infrastructure/file_provider.py: 73%
src/domain/workflow.py: 72%
```

### 4.3 根本原因
- **副作用が多いコード**: テストが書きにくい
- **ユーティリティ軽視**: 「単純だから」という理由でテストを省略
- **時間的制約**: 「後でテストを書く」が実現されない

### 4.4 影響
- バグの発見が遅れる
- リファクタリングへの恐怖
- 品質の保証ができない

## 5. 短期的解決（temporary workaround）の蓄積

### 5.1 発生状況
- **明示的なコメント**: 3箇所
- **暗黙的な短期的解決**: 多数

### 5.2 典型的な失敗パターン
```python
# BAD: 明示的な一時的回避策
def execute_workflow(self):
    # Temporary workaround for TEST steps allow_failure issue
    if step.type == "TEST":
        step.allow_failure = True  # 違反：短期的解決

# BAD: 一時的な命名
def format_output(self):
    # temporary simple naming
    return f"output_{timestamp}"  # 違反：適切な設計の欠如
```

### 5.3 根本原因
- **時間的プレッシャー**: 「今動かす」ことを優先
- **技術的負債の軽視**: 「後で直す」が実現されない
- **設計の不備**: 適切な解決策が見つからない

### 5.4 影響
- コードの品質低下
- 保守性の悪化
- 「temporary」が恒久化

## 改善に向けた提言

### 1. 即座に実施すべきこと
1. **src_checkツールの修正と実行**
   - インポートパスの修正
   - 全違反箇所の自動検出
   
2. **最も影響の大きい違反から修正**
   - Infrastructure層以外の副作用を最優先で移動
   - デフォルト値の完全除去

### 2. 段階的な改善計画
1. **Phase 1**: 副作用の移動（1-2週間）
2. **Phase 2**: デフォルト値とフォールバックの除去（2-3週間）
3. **Phase 3**: テストカバレッジ向上（3-4週間）
4. **Phase 4**: アーキテクチャの簡素化（4-6週間）

### 3. 失敗を繰り返さないための施策
1. **自動チェックの強化**
   - pre-commitフックでの違反検出
   - CI/CDでの品質ゲート
   
2. **設計レビューの徹底**
   - CLAUDE.md準拠の確認
   - 中長期視点での評価
   
3. **技術的負債の可視化**
   - 定期的な違反レポートの生成
   - 改善進捗の追跡

## まとめ
これらの失敗パターンは、短期的な利便性を優先し、CLAUDE.mdの規約を軽視した結果生じています。根本的な解決には、開発文化の変革と、継続的な品質改善への取り組みが必要です。