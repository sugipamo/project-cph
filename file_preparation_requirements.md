# ファイル準備機能 要件・設計書

## 概要

競技プログラミング支援ツールにおけるファイル準備機能の要件と設計方針を整理したドキュメント。

## 1. 基本要件

### 1.1 ワークフロー統一
- **目標**: Python と C++ で同じワークフロー構造を使用
- **理由**: 保守性向上、一貫したユーザー体験、設計の簡素化

### 1.2 操作の種類
1. **workspace_switch**: ワークスペース切り替え（アーカイブ→復元）
2. **move_test_files**: テストファイルの移動（workspace → contest_current）

## 2. 統一ワークフロー設計

### 2.1 共通実行順序（Python & C++）
```json
[
  {
    "type": "file_preparation",
    "operation_type": "workspace_switch",
    "allow_failure": false
  },
  {
    "type": "python", 
    "description": "ブラウザでコンテストページを開く"
  },
  {
    "type": "shell",
    "description": "エディタを開く"
  },
  {
    "type": "oj",
    "description": "テストケースをダウンロード"
  },
  {
    "type": "file_preparation",
    "operation_type": "move_test_files", 
    "allow_failure": true
  }
]
```

### 2.2 設計決定の背景

#### C++ の手動copyアプローチを廃止
**理由**:
- 不完全な状態管理（単一ファイルのみ）
- エラーハンドリングの欠如
- 操作順序の問題（アーカイブ→復元が逆）
- 統一性の欠如

#### workspace_switchの採用
**利点**:
- 包括的な状態管理
- エラーハンドリングと適切なロールバック
- 操作履歴の記録
- テンプレート・アーカイブ両方のサポート

## 3. ファイル移動方針

### 3.1 現在の実装アプローチ（推奨）
**方式**: ディレクトリ全体移動
```python
# workspace/test → contest_current/test
self.file_driver.move(source_path, dest_path)
```

### 3.2 他の候補アプローチ（非推奨）
**方式**: DB登録ベースの選択的移動
**非推奨理由**:
- 競技プログラミングツールとして過剰設計
- 複雑性が価値を上回る
- DB登録漏れのリスク
- パフォーマンス劣化

### 3.3 技術的判断根拠

#### 現在アプローチの利点
- **シンプルさ**: 理解しやすく、バグが少ない
- **確実性**: すべてのファイルが確実に移動
- **パフォーマンス**: 1回の操作で完了
- **一般性**: ojtools以外のツールにも対応

#### KISS・YAGNI原則の適用
- **KISS**: Keep It Simple, Stupid
- **YAGNI**: You Aren't Gonna Need It
- 競技プログラミングでは全テストファイル移動が標準的

## 4. データベース管理方針

### 4.1 保持すべき情報（操作履歴）
**テーブル**: `file_preparation_operations`
```sql
CREATE TABLE file_preparation_operations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    language_name TEXT NOT NULL,
    contest_name TEXT NOT NULL, 
    problem_name TEXT NOT NULL,
    operation_type TEXT NOT NULL,        -- 'move_test_files', 'workspace_switch', etc.
    source_path TEXT NOT NULL,
    destination_path TEXT NOT NULL,
    file_count INTEGER DEFAULT 0,
    success BOOLEAN NOT NULL DEFAULT 0,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**保持理由**:
- デバッグ・トラブルシューティングで価値
- 実装コストが軽い
- 実際の問題解決に直接役立つ

### 4.2 削除すべき情報（個別ファイル追跡）
**テーブル**: `contest_current_files` ❌削除対象

**削除理由**:
- 競技プログラミングツールとして過剰設計
- 複雑さ vs 価値のミスマッチ
- 保守コストの増大
- ユーザーが求めていない機能

### 4.3 代替アプローチ（推奨）
**方式**: シンプルなファイルシステムベース
```
contest_current/
├── main.cpp
├── test/
│   ├── sample-1.in
│   └── sample-1.out
└── .metadata (シンプルなメタデータファイル)
```

**利点**:
- 透明性（ファイルシステムで直接確認可能）
- シンプルさ（DBなしで状態管理）
- 信頼性（ファイルシステムの整合性に依存）
- デバッグ容易性（ファイルを直接確認可能）

## 5. 実装指針

### 5.1 統一設計の適用
1. **C++**: 手動copyステップを削除し、workspace_switchを追加
2. **Python**: 既存のworkspace_switch + move_test_files構造を維持
3. **共通**: operation_typeによる統一的な操作管理

### 5.2 サービス層の責務
- **ProblemWorkspaceService**: ワークスペース全体の状態管理
- **FilePreparationService**: ファイル移動操作とその履歴管理

### 5.3 エラーハンドリング
- workspace_switch: `allow_failure = false`（失敗時は停止）
- move_test_files: `allow_failure = true`（失敗しても継続）

## 6. 期待される効果

### 6.1 保守性の向上
- 両言語で同じロジック・サービスを使用
- 設計の一貫性によるバグ削減
- 新機能追加時の両言語同時対応

### 6.2 信頼性の向上  
- シンプルな実装による障害減少
- 適切なエラーハンドリング
- 操作履歴による問題診断能力

### 6.3 ユーザー体験の向上
- 一貫したワークフロー
- 高速で確実なファイル操作
- 問題発生時の迅速な原因特定

## 7. 今後の作業項目

### 7.1 即座に実装すべき項目
1. C++のenv.jsonからmanual copyステップを削除 ✅完了
2. C++にworkspace_switch操作を追加 ✅完了
3. 両言語のワークフロー統一 ✅完了

### 7.2 検討・改善項目
1. `contest_current_files`テーブルの削除検討
2. シンプルなメタデータファイルシステムの検討
3. 操作履歴の活用（デバッグコマンド等）

## 8. 設計決定の履歴

| 日付 | 決定事項 | 理由 |
|------|----------|------|
| 2025-01-09 | ワークフロー統一方針決定 | 保守性・一貫性向上 |
| 2025-01-09 | DB個別ファイル追跡廃止決定 | 過剰設計の排除 |
| 2025-01-09 | 操作履歴保持決定 | デバッグ価値 vs 軽量コスト |
| 2025-01-09 | ディレクトリ全体移動方式維持 | KISS・YAGNI原則適用 |

---

**最終更新**: 2025-01-09  
**レビュー**: 技術的合理性・実用性の観点から第三者評価済み