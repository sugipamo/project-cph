# 設定ベース移行分析レポート

## 概要

env.json側でコマンドの実行方法を持つことで、コードの変更による機能の破壊の可能性が格段に低くなったことを踏まえ、プロジェクト上に設定ベースに移行するべき手続き型処理を分析しました。

## 現在の設定ベースアプローチの特徴

### 主要パターン

1. **コマンド定義パターン**
   - 構造化されたステップでコマンドを完全に設定駆動
   - テンプレート変数による動的パス解決
   - 実行条件（`when`）とエラー処理（`allow_failure`）

2. **階層デフォルトパターン**
   - システム設定 → 共有設定 → 言語設定 → ランタイム設定の優先順位
   - 型安全な設定解決（`TypeSafeConfigNodeManager`）

3. **エラー分類と再試行ポリシー**
   - 設定による構造化エラーハンドリング
   - 再試行可能例外の定義

## 高優先度移行候補

### 1. Docker Command Builder
**場所**: `src/infrastructure/drivers/docker/utils/docker_command_builder.py`

**現在の問題**:
```python
def build_docker_run_command(image: str, name: str, options: dict[str, Any]) -> list[str]:
    cmd = ["docker", "run"]
    cmd.extend(["--name", name])
    _add_docker_run_flags(cmd, options)
    # ハードコードされたコマンド構築
```

**移行案**:
```json
{
  "docker_commands": {
    "run": {
      "base_template": ["docker", "run", "--name", "{name}"],
      "option_handlers": {
        "ports": {"template": ["-p", "{host_port}:{container_port}"]},
        "volumes": {"template": ["-v", "{host_path}:{container_path}"]}
      }
    }
  }
}
```

### 2. Workflow Step Execution
**場所**: `src/workflow/workflow_execution_service.py`

**現在の問題**:
```python
def execute_workflow(self, parallel, max_workers):
    # 固定のパイプライン処理
    operations_composite, errors, warnings = self._prepare_workflow_steps()
    preparation_results, prep_errors = self._execute_preparation_phase(operations_composite)
    results = self._execute_main_workflow(operations_composite, use_parallel, use_max_workers)
```

**移行案**:
```json
{
  "workflow_phases": {
    "standard": [
      {"name": "prepare", "allow_failure": false, "parallel": false},
      {"name": "execute", "allow_failure": false, "parallel": true},
      {"name": "analyze", "allow_failure": true, "parallel": false}
    ]
  },
  "error_handling": {
    "preparation_failure": "abort",
    "execution_failure": "continue_with_warning"
  }
}
```

### 3. E2E Test Procedures （別タスク）
**場所**: `scripts/e2e.py`

**注意**: テスト環境の設定ベース移行は本番環境への混入を防ぐため、別タスクとして分離して実施する。

## 中優先度移行候補

### 4. Step Generation Pipeline
**場所**: `src/workflow/step/workflow.py`

**現在の問題**: 生成→検証→解決→最適化の固定パイプライン

**移行案**: パイプライン段階の設定化、プラガブル最適化戦略

### 5. File Operation Dispatching
**場所**: `src/operations/requests/file/file_request.py`

**現在の問題**: if-elif による操作振り分け

**移行案**: オペレーションハンドラーマッピングの設定化

## 移行による効果

### メリット
1. **機能破壊リスクの大幅削減**
   - コード変更なしで動作変更が可能
   - 設定ミスは実行時に明確にエラー表示

2. **保守性の向上**
   - 手続きロジックと設定の分離
   - 環境固有のカスタマイズが容易

3. **テスト性の向上**
   - 異なる設定でのテストが簡単
   - モック設定の作成が容易

### 移行指針

1. **段階的移行**
   - 既存機能の互換性を保ちながら設定オプションを追加
   - 設定ファイルが存在しない場合のフォールバック（ただし警告表示）

2. **設定検証の強化**
   - JSON Schema による設定検証
   - 起動時の設定妥当性チェック

3. **テンプレート機能の活用**
   - 既存の `{contest_current_path}` パターンを拡張
   - 条件付きテンプレート展開

## 実装推奨順序

1. **Docker Command Builder** - 影響範囲が限定的で効果が高い
2. **Workflow Step Execution** - 中核機能だが影響範囲が大きいため慎重に
3. **Step Generation Pipeline** - 他の移行完了後に検討
4. **File Operation Dispatching** - 最後に実施（影響範囲が最も大きい）

**注意**: E2E Test Procedures は別タスクとして分離

## 注意事項

- **CLAUDE.mdの制約遵守**: デフォルト値の使用禁止、設定ファイル編集は明示的指示時のみ
- **互換性維持**: 既存のenv.jsonパターンとの整合性保持
- **エラーハンドリング**: フォールバック処理禁止の原則に従い、必要なエラーを適切に表面化