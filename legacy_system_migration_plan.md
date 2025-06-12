# 設定管理システム レガシー移行計画

## 概要

新設定管理システムの実装が完了し、現在は段階的移行フェーズにあります。この文書では、旧システムから新システムへの完全移行と、レガシーコードの安全な削除計画を示します。

## 現状分析

### ✅ 移行完了済み
- **新設定システム実装**: 完全実装済み（45テスト成功）
- **user_input_parser.py**: 新システムで動作中（フォールバック付き）
- **simple_step_runner.py**: 新システム対応済み
- **ExecutionContextAdapter**: 責務分離済み
- **言語レジストリ**: 動的設定対応済み

### ⚠️ 移行途中
- **workflow_execution_service.py**: 旧ExecutionContextに依存
- **テストファイル群**: 一部が旧システム前提
- **フォールバック機能**: user_input_parserに残存

### ❌ 削除対象（移行後）
- **旧ExecutionContext**: 循環依存の原因
- **分散変数展開関数**: 32個→1個に統合済み
- **重複設定クラス**: 5個→1個に統合済み

## 移行計画

### フェーズA: 残存依存関係の完全移行 (期間: 2週間)

#### A1. workflow_execution_service.pyの移行 (3-4日)

**現状問題:**
```python
# src/workflow/workflow_execution_service.py:7
from src.context.execution_context import ExecutionContext

class WorkflowExecutionService:
    def __init__(self, context: ExecutionContext, operations):
        self.context = context  # 旧システム依存
```

**移行作業:**
```python
# 新実装
from src.configuration.adapters.execution_context_adapter import ExecutionContextAdapter

class WorkflowExecutionService:
    def __init__(self, context: ExecutionContextAdapter, operations):
        self.context = context  # 新システム対応
```

**チェックリスト:**
- [ ] WorkflowExecutionServiceの新システム対応
- [ ] 関連テストの動作確認
- [ ] 統合テストでのワークフロー実行確認
- [ ] パフォーマンス検証

#### A2. テストファイルの移行 (3-4日)

**移行対象ファイル:**
```
tests/base/base_test.py
tests/context/test_user_input_parser_extended.py
tests/context/test_docker_naming_integration.py
src/context/utils/validation_utils.py
```

**移行戦略:**
1. テストを新システムベースに書き換え
2. モックオブジェクトを新システム対応に更新
3. 既存テスト動作確認
4. 新機能テスト追加

**チェックリスト:**
- [ ] 旧ExecutionContext依存テストの洗い出し
- [ ] 新システム用テストヘルパー作成
- [ ] テスト一つずつの移行
- [ ] 回帰テスト実行

#### A3. 隠れた依存関係の調査・修正 (2-3日)

**調査対象:**
```bash
# 依存関係の網羅的調査
grep -r "ExecutionContext" src/ --include="*.py" | grep -v "configuration"
grep -r "format_string" src/ --include="*.py" | grep -v "configuration"
grep -r "expand_template" src/ --include="*.py" | grep -v "configuration"
```

**チェックリスト:**
- [ ] 全プロジェクトでの依存関係調査
- [ ] 見つかった依存関係の移行
- [ ] インポート文の整理
- [ ] 未使用コードの特定

### フェーズB: フォールバック機能の段階的除去 (期間: 1週間)

#### B1. user_input_parserの新システム専用化 (3-4日)

**現状のフォールバック:**
```python
# src/context/user_input_parser.py:282-325
try:
    new_context = create_new_execution_context(...)
    old_context = ExecutionContext(...)  # ← この部分を除去
    
    if integration.validate_new_system_compatibility(old_context, new_context):
        context = new_context
    else:
        context = old_context  # ← フォールバック除去
except:
    context = ExecutionContext(...)  # ← 例外時フォールバック除去
```

**新実装:**
```python
# フォールバック除去後
context = create_new_execution_context(
    command_type=current_context_info["command"],
    language=current_context_info["language"],
    contest_name=current_context_info["contest_name"],
    problem_name=current_context_info["problem_name"],
    env_type=current_context_info["env_type"],
    env_json=final_env_json
)
```

**チェックリスト:**
- [ ] フォールバック機能の段階的無効化
- [ ] 新システム専用での動作確認
- [ ] エラーハンドリングの改善
- [ ] 1週間の本格運用での安定性確認

#### B2. 新システムでの包括的テスト (2-3日)

**テスト項目:**
```
1. 全言語での動作確認（Python, C++, Rust, Java...）
2. 全コマンドタイプでの動作確認
3. 設定変更時の動作確認
4. エラー状況での動作確認
5. パフォーマンステスト
```

**チェックリスト:**
- [ ] E2Eテストの実行
- [ ] ストレステストの実行
- [ ] メモリリークテスト
- [ ] 大規模設定でのテスト

### フェーズC: レガシーシステムの完全削除 (期間: 1週間)

#### C1. 削除対象ファイルの特定・削除 (2-3日)

**削除対象ファイル:**
```
src/context/execution_context.py              # 旧ExecutionContext
src/context/config_resolver_proxy.py          # 循環依存の原因
src/context/execution_data.py                 # 重複データクラス
src/context/formatters/context_formatter.py   # 分散フォーマット関数
tests/context/test_execution_context.py       # 旧システムテスト
```

**削除手順:**
1. 各ファイルの最終依存関係確認
2. 段階的削除（重要度の低いファイルから）
3. 削除後の動作確認
4. テスト実行での影響確認

#### C2. インポート文とコメントの整理 (1-2日)

**整理対象:**
```python
# 不要なインポート削除
from src.context.execution_context import ExecutionContext  # 削除
from src.utils.formatters import format_string_simple       # 削除

# コメント更新
# TODO: 旧システムから移行  # 削除
# FIXME: ExecutionContext依存  # 削除
```

#### C3. 最終検証とドキュメント更新 (1-2日)

**検証項目:**
- [ ] 全機能テスト
- [ ] パフォーマンステスト
- [ ] メモリ使用量確認
- [ ] ドキュメント更新

## リスク管理

### 高リスク項目

#### 1. 隠れた依存関係
**リスク:** 見落とした依存関係により実行時エラー
**対策:** 段階的削除 + 包括的テスト

#### 2. パフォーマンス劣化
**リスク:** 新システムでの予期しない性能問題
**対策:** 各フェーズでのベンチマーク実施

#### 3. 設定の互換性問題
**リスク:** 既存設定との非互換性
**対策:** 移行テストスイートの実行

### 緊急時対応

#### ロールバック手順
```bash
# 1. 緊急時の旧システム復旧
git checkout HEAD~1 src/context/execution_context.py
git checkout HEAD~1 src/context/user_input_parser.py

# 2. フォールバック機能の再有効化
# user_input_parser.pyでのフォールバック復旧

# 3. 動作確認
python3 -m pytest tests/context/
```

## 移行後の期待効果

### 即座の効果
- **コードサイズ削減**: 約2000行の削除
- **循環依存解消**: ExecutionContext関連の依存問題解決
- **メンテナンス性向上**: 責務分離による保守容易性

### 長期的効果
- **新機能開発の高速化**: 明確なアーキテクチャによる開発効率向上
- **バグ削減**: 不変データ構造による信頼性向上
- **拡張性向上**: 新言語・新機能の追加容易性

## マイルストーン

| フェーズ | 期間 | 完了予定 | 主要成果物 |
|---------|------|----------|------------|
| **A** | 2週間 | Week 3 | 全依存関係移行完了 |
| **B** | 1週間 | Week 4 | フォールバック除去完了 |
| **C** | 1週間 | Week 5 | レガシー削除完了 |

## 完了条件

### 技術的完了条件
- [ ] 全テスト成功（45 + α個）
- [ ] パフォーマンス基準クリア（400展開/秒以上）
- [ ] メモリ使用量改善確認
- [ ] E2Eテスト成功

### プロセス完了条件
- [ ] コードレビュー完了
- [ ] ドキュメント更新完了
- [ ] ナレッジ共有完了
- [ ] 本番環境での安定稼働確認（1週間）

## 責任者・連絡先

**移行責任者:** 開発チーム
**レビュー担当:** アーキテクト
**緊急連絡先:** [連絡先情報]

---

## 付録

### 新旧システム対応表

| 旧システム | 新システム | 状態 |
|------------|------------|------|
| ExecutionContext | ExecutionContextAdapter | ✅ 移行済み |
| 32個の変数展開関数 | TemplateExpander | ✅ 統合済み |
| 5個の重複コンテキスト | ExecutionConfiguration | ✅ 統合済み |
| JsonConfigLoader | ConfigurationLoader | ✅ 改善済み |
| ConfigNode | ConfigurationResolver | ✅ 統合済み |

### 参考資料
- [configuration_redesign_proposal.md](./configuration_redesign_proposal.md)
- [新設定管理システム設計書](./src/configuration/__init__.py)
- [テスト結果レポート](./tests/configuration/)

---

**最終更新:** 2025年12月6日
**バージョン:** 1.0
**ステータス:** 承認待ち