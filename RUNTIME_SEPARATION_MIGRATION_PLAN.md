# Runtime分離の段階的移行計画

## 概要
4層設定システム（system/shared/language/runtime）から、設定システム（3層）と状態管理システムの分離を段階的に実行する計画。

## 移行戦略: 3段階アプローチ

### Phase 1: 新システムの並行稼働 (1-2週間)
**目標**: 既存システムを維持しながら新システムを並行稼働

#### 実装済み項目
✅ **インターフェース設計**
- `ISettingsManager` - 設定管理の統一インターフェース
- `IExecutionSettings` - 実行設定のインターフェース  
- `IRuntimeSettings` - Runtime設定のインターフェース
- `IStateManager` - 状態管理のインターフェース

✅ **状態管理システム**
- `SqliteStateManager` - SQLiteベースの状態管理実装
- `ExecutionHistory` - 実行履歴データ構造
- `SessionContext` - セッションコンテキスト管理

✅ **純粋設定システム**
- `PureSettingsManager` - 3層設定システム実装
- `PureExecutionSettings` - 純粋な実行設定
- `PureRuntimeSettings` - 純粋なRuntime設定

✅ **統一アダプター**
- `UnifiedExecutionAdapter` - 既存インターフェース互換アダプター

#### 次の実装項目
🔄 **Phase 1 残りタスク**:
1. **ファクトリーパターンの実装**
   ```python
   # src/configuration/factories/separated_system_factory.py
   class SeparatedSystemFactory:
       def create_unified_adapter() -> UnifiedExecutionAdapter
   ```

2. **フィーチャーフラグによる切り替え**
   ```python
   # config/dev_config.json に追加
   "feature_flags": {
       "use_separated_runtime_system": false  # 段階的に true に変更
   }
   ```

3. **既存システムとの並行テスト**
   - 同一入力での動作比較
   - 出力結果の整合性検証

### Phase 2: 段階的置き換え (2-4週間)
**目標**: 高リスク箇所から段階的に新システムに切り替え

#### 置き換え順序
1. **テストファイル** → 低リスク、影響範囲限定
2. **WorkflowExecutionService** → 中リスク、重要機能
3. **user_input_parser.py** → 高リスク、中核機能
4. **ExecutionContextAdapter** → 最高リスク、全体影響

#### 実装手順
```python
# 段階的置き換えのサンプル
class WorkflowExecutionServiceV2:
    def __init__(self, use_separated_system: bool = False):
        if use_separated_system:
            self.adapter = SeparatedSystemFactory.create_unified_adapter()
        else:
            self.adapter = ExistingExecutionContextAdapter()
```

### Phase 3: 完全移行とクリーンアップ (1-2週間)  
**目標**: 既存システムの完全削除と最適化

#### 削除対象
- `RuntimeConfig` クラス（設定部分）
- `ExecutionConfiguration` の runtime 依存部分
- 旧 `ExecutionContextAdapter`
- runtime関連の複雑な条件分岐

#### 最適化項目
- 不要な抽象化レイヤーの削除
- パフォーマンス最適化
- ドキュメント更新

## 分離後のシステム構成

### 設定システム（純化済み）
```
system層 (config/system/*.json)
  ├── システム定数
  ├── Docker設定  
  └── 開発設定
     ↓
shared層 (contest_env/shared/env.json)
  ├── 共通パス設定
  ├── コマンド定義
  └── ファイルパターン
     ↓  
language層 (contest_env/{language}/env.json)
  ├── 言語固有設定
  ├── Runtime設定データ
  └── 実行コマンド
```

### 状態管理システム（独立）
```
StateManager (SQLite)
  ├── ExecutionHistory (実行履歴)
  ├── SessionContext (セッション状態)
  └── UserSpecifiedValues (ユーザー指定値)
```

### 統一アダプター（互換性）
```
UnifiedExecutionAdapter
  ├── SettingsManager (設定システム)
  ├── StateManager (状態管理システム)  
  └── 既存API互換メソッド
```

## 期待される効果

### 1. アーキテクチャの改善
- **責務の明確化**: 設定 vs 状態の分離
- **依存関係の単純化**: 層間依存の削減
- **テスタビリティ向上**: 独立テスト可能

### 2. 保守性の向上
- **設定変更の影響縮小**: 状態に影響しない設定変更
- **バグ修正の効率化**: 問題箇所の特定が容易
- **新機能追加の容易化**: 明確な責務分界

### 3. 拡張性の向上  
- **新設定タイプの追加**: 状態管理に影響なし
- **異なる永続化方式**: 設定と状態で独立選択可能
- **設定管理機能の拡張**: 状態管理の制約なし

## リスク軽減策

### 1. 技術的リスク
- **回帰テスト**: 各Phase後の動作検証
- **A/Bテスト**: 新旧システムの並行実行
- **ロールバック計画**: 問題発生時の復旧手順

### 2. 運用リスク
- **段階的リリース**: 機能ごとの段階的展開
- **モニタリング**: 設定・状態管理の動作監視
- **ドキュメント**: 変更点の明確な記録

### 3. 品質リスク
- **互換性テスト**: 既存APIとの完全互換性
- **パフォーマンステスト**: 処理速度の劣化防止
- **セキュリティ検証**: 新システムの安全性確認

## 成功指標

### 定量的指標
- **設定関連ファイル数**: 21個 → 15個以下（30%削減）
- **設定管理コード行数**: 3000行 → 2000行以下（33%削減）
- **テスト実行時間**: 現在の95%以下を維持

### 定性的指標
- **開発者体験**: 設定変更の理解が容易
- **新機能追加**: 状態に影響しない設定変更が可能
- **バグ対応**: 問題箇所の特定時間短縮

## 次のアクション

### 即時実行項目
1. **SeparatedSystemFactory** の実装
2. **フィーチャーフラグ** の設定
3. **並行テスト環境** の構築

### 継続監視項目
- 新システムの動作安定性
- 既存システムとの整合性
- パフォーマンス影響の測定

この移行計画により、リスクを最小化しながらシステムの根本的改善を実現できると評価しています。

## 実装状況

### ✅ 完了項目
- インターフェース設計（5ファイル）
- 状態管理システム（2ファイル）  
- 純粋設定システム（1ファイル）
- 統一アダプター（1ファイル）
- 移行計画策定

### 🔄 進行中項目
- ファクトリーパターン実装
- フィーチャーフラグ設定
- 並行テスト環境構築

### 📋 残りタスク
- 段階的置き換え実装
- 既存システム削除
- 最適化とクリーンアップ