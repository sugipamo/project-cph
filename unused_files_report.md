# 未使用ファイル調査レポート

## 調査結果サマリー

- 全ソースファイル数: 176
- 未使用の可能性があるファイル数: 73 (41%)
- 完全に未使用（未使用かつカバレッジ0%）: 10ファイル

## 削除候補ファイル（優先度: 高）

以下のファイルは、どこからも使用されておらず、テストカバレッジも0%のため、削除を検討できます：

1. `src/env_core/step/simple_graph_analysis.py` - グラフ分析機能（未実装）
2. `src/env_core/types.py` - 型定義ファイル（未使用）
3. `src/env_core/workflow/application/step_to_request_adapter.py` - アダプター（未使用）
4. `src/env_core/workflow/domain/workflow_domain_service.py` - ドメインサービス（未使用）
5. `src/env_core/workflow/infrastructure/request_infrastructure_service.py` - インフラサービス（未使用）
6. `src/env_core/workflow/layered_workflow_builder.py` - レイヤー型ワークフロービルダー（未使用）
7. `src/env_factories/request_builders.py` - リクエストビルダー（未使用）
8. `src/env_integration/fitting/environment_inspector.py` - 環境検査機能（未使用）
9. `src/env_integration/fitting/preparation_planner.py` - 準備計画機能（未使用）
10. `src/factories/factory_coordinator.py` - ファクトリーコーディネーター（未使用）

## リファクタリング候補（優先度: 中）

以下のシステムは、テストでは使用されているが、実際のメインフローからは到達不可能です：

### 1. 設定管理システム (`src/config/*`)
- 新しいシステムに移行済み？
- 7ファイル、カバレッジあり

### 2. エラーハンドリングシステム (`src/core/exceptions/*`)
- 新しいエラーハンドリングに移行済み？
- 5ファイル、カバレッジあり

### 3. 環境ファクトリーシステム (`src/env_factories/*`)
- 別の実装に置き換えられた？
- 11ファイル、一部カバレッジあり

### 4. 環境統合システム (`src/env_integration/*`)
- 新しい統合方式に移行？
- 6ファイル、一部カバレッジあり

## 調査が必要なファイル（優先度: 低）

以下は`__init__.py`ファイルで、パッケージマーカーとして必要な可能性があります：

- `src/cli/__init__.py` - CLIパッケージ（カバレッジ0%だが使用されている）
- `src/environment/__init__.py` - 環境パッケージ（同上）
- `src/infrastructure/__init__.py` - インフラパッケージ（同上）
- `src/workflow/__init__.py` - ワークフローパッケージ（同上）

## 推奨アクション

1. **即座に削除可能**: 上記の「削除候補ファイル」10個
2. **段階的削除**: リファクタリング候補のシステムを、機能確認後に削除
3. **保持**: `__init__.py`ファイルは、インポートエラーを避けるため保持

## 削除による影響

- **コード量削減**: 約40%のファイルを削除可能
- **メンテナンス性向上**: 未使用コードの混乱を解消
- **テストカバレッジ向上**: 分母が減ることで全体のカバレッジ率が向上

## 注意事項

- 削除前に、本番環境での動作確認を推奨
- 段階的な削除（ブランチごと）を推奨
- 削除前にバックアップまたはGitタグの作成を推奨