# カバレッジ改善計画

## 現在の状況

### テスト実行結果
- **総カバレッジ**: 67% (7291行中4867行カバー)
- **テスト失敗**: 14件
- **テスト成功**: 864件  
- **スキップ**: 13件

### 品質チェック
- **ruff警告**: 5件（主にwith文のネスト問題）

## 低カバレッジモジュール（優先改善対象）

### 1. Workflow準備系（最優先）
- `workflow/preparation/transition_engine.py`: 14% (221行中189行未カバー)
- `workflow/preparation/preparation_executor.py`: 18% (263行中215行未カバー)
- `workflow/preparation/environment_inspector.py`: 21% (179行中141行未カバー)
- `workflow/workflow_execution_service.py`: 14% (105行中90行未カバー)

### 2. Context系
- `context/config_resolver_proxy.py`: 17% (36行中30行未カバー)
- `context/parsers/validation_service.py`: 22% (54行中42行未カバー)

### 3. Infrastructure系
- `infrastructure/environment/environment_manager.py`: 30% (127行中89行未カバー)
- `infrastructure/persistence/sqlite/fast_sqlite_manager.py`: 38% (139行中86行未カバー)

## 改善アクション

### フェーズ1: 失敗テストの修正
1. **CLI Application JSONデコードエラー**
   - `tests/application/test_cli_application.py::test_run_json_decode_error`を修正

2. **User Input Parser関連**
   - `tests/context/test_user_input_parser_extended.py`の10件の失敗テストを修正
   - `apply_language`, `apply_env_type`, `apply_command`等の機能テスト

3. **Persistence関連**
   - `tests/persistence/test_system_config_repository.py`の3件の失敗テストを修正

### フェーズ2: Workflow準備系カバレッジ向上
1. **TransitionEngine**: 目標カバレッジ 50%
   - 状態遷移ロジックのテスト追加
   - エラーハンドリングのテストケース追加

2. **PreparationExecutor**: 目標カバレッジ 50%
   - 準備実行フローのテスト追加
   - 例外処理のテストケース追加

3. **EnvironmentInspector**: 目標カバレッジ 50%
   - 環境検査ロジックのテスト追加

### フェーズ3: Context系カバレッジ向上
1. **ConfigResolverProxy**: 目標カバレッジ 60%
   - 設定解決プロキシのテスト追加

2. **ValidationService**: 目標カバレッジ 70%
   - バリデーション機能のテスト追加

### フェーズ4: Infrastructure系カバレッジ向上
1. **EnvironmentManager**: 目標カバレッジ 70%
   - 環境管理機能のテスト追加

2. **FastSQLiteManager**: 目標カバレッジ 70%
   - SQLite高速操作のテスト追加

## 品質改善

### Ruff警告の修正
1. **SIM117警告**: with文のネスト解消
   - `tests/application/test_cli_application.py:237`
   - `tests/context/test_user_input_parser_extended.py:272,409,435`
   - `tests/persistence/test_system_config_repository.py:119`

## 目標

### 短期目標（1-2週間）
- 失敗テストの修正（100%）
- 総カバレッジ 75%達成
- Ruff警告の完全解消

### 中期目標（1ヶ月）
- 総カバレッジ 80%達成
- 全モジュール最低50%カバレッジ達成

### 長期目標（2ヶ月）
- 総カバレッジ 85%達成
- クリティカルモジュール 90%カバレッジ達成

## 実施スケジュール

| 週 | 作業内容 | 期待カバレッジ |
|---|---------|-------------|
| 1 | 失敗テスト修正 + Ruff警告修正 | 67% → 70% |
| 2 | Workflow準備系テスト追加 | 70% → 75% |
| 3 | Context系テスト追加 | 75% → 78% |
| 4 | Infrastructure系テスト追加 | 78% → 80% |

## 注意事項

- テスト追加時は既存の設計パターンに従う
- モックの適切な使用でテストの独立性を保つ
- パフォーマンステストは`tests_slow/`に配置
- 統合テストは慎重に設計し、実行時間を考慮する