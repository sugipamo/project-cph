# 品質基準の選択的適用戦略

## 現状の問題

- 複雑なロジックには50行制限が非現実的
- 基準を全面的に緩和すると品質悪化のリスク
- 一律適用では開発効率が低下

## 提案: 階層化品質基準システム

### 1. コンテキスト別品質基準

#### A. コアロジック層 (Core Logic)
**適用範囲**: 
- `_execute_core`関数
- `classify_error`関数
- `parse_user_input`関数
- 状態機械やパイプライン処理

**緩和された基準**:
- 関数サイズ: 80行まで許可
- 複雑度: 高い複雑度を許可
- 条件: 単一責任の原則を満たす場合

#### B. 通常ビジネスロジック層 (Business Logic)
**適用範囲**: アプリケーション層、ドメイン層の通常関数

**標準基準**:
- 関数サイズ: 50行
- 複雑度: 中程度まで
- 単一責任の原則厳守

#### C. ユーティリティ層 (Utility)
**適用範囲**: utils、helpers、単純な処理

**厳格基準**:
- 関数サイズ: 30行
- 複雑度: 低い
- 純粋関数推奨

### 2. 自動判定ロジック

```python
def determine_quality_tier(function_name: str, file_path: str, node: ast.FunctionDef) -> str:
    # コアロジック判定
    if function_name in ['_execute_core', 'classify_error', 'parse_user_input']:
        return 'core_logic'
    
    # パターンマッチング
    if 'state_machine' in function_name or 'pipeline' in function_name:
        return 'core_logic'
    
    # ユーティリティ判定
    if '/utils/' in file_path or '/helpers/' in file_path:
        return 'utility'
    
    # デフォルト
    return 'business_logic'
```

### 3. 品質悪化防止措置

#### A. 補償的チェック強化
コアロジック層で関数サイズを緩和する代わりに:

1. **文書化要件**:
   - 関数の責任を明確に記述
   - 複雑な部分にコメント必須
   - 分割できない理由を文書化

2. **テストカバレッジ要件**:
   - 90%以上のカバレッジ必須
   - エッジケースのテスト強化
   - 統合テストの追加

3. **レビュー要件**:
   - 複数人によるコードレビュー必須
   - アーキテクト承認が必要

#### B. 品質メトリクスの多様化

従来の行数だけでなく:
- **循環複雑度** (Cyclomatic Complexity)
- **認知複雑度** (Cognitive Complexity)
- **結合度** (Coupling)
- **凝集度** (Cohesion)

### 4. 実装アプローチ

#### Phase 1: 階層化システム導入
```python
# practical_quality_check.py に追加
QUALITY_TIERS = {
    'core_logic': {
        'max_lines': 80,
        'max_complexity': 15,
        'require_docs': True,
        'min_test_coverage': 90
    },
    'business_logic': {
        'max_lines': 50,
        'max_complexity': 10,
        'require_docs': False,
        'min_test_coverage': 80
    },
    'utility': {
        'max_lines': 30,
        'max_complexity': 5,
        'require_docs': False,
        'min_test_coverage': 95
    }
}
```

#### Phase 2: 警告レベルの細分化
- **ERROR**: 絶対に許可しない違反
- **WARNING**: 改善推奨だが許可
- **INFO**: 品質向上のための提案

#### Phase 3: 継続的モニタリング
- 品質メトリクスの推移追跡
- 技術的負債の定量化
- 定期的な基準見直し

### 5. 具体的な設定例

```yaml
# quality_config.yaml
tiers:
  core_logic:
    patterns:
      - "*_execute_core"
      - "classify_error"
      - "parse_user_input"
    limits:
      max_lines: 80
      max_complexity: 15
    requirements:
      documentation: required
      test_coverage: 90
      
  business_logic:
    patterns:
      - "src/application/**"
      - "src/domain/**"
    limits:
      max_lines: 50
      max_complexity: 10
      
  utility:
    patterns:
      - "src/utils/**"
      - "src/helpers/**"
    limits:
      max_lines: 30
      max_complexity: 5
```

## 期待される効果

1. **品質維持**: 重要でない部分での品質低下を防止
2. **開発効率**: 複雑なロジックでの無駄な分割作業を削減
3. **明確な基準**: コンテキストに応じた適切な品質基準
4. **継続的改善**: メトリクスに基づく客観的な品質管理

## リスク軽減策

1. **段階的導入**: 一部の関数から開始し、効果を検証
2. **定期的レビュー**: 3ヶ月ごとに基準の妥当性を確認
3. **チーム教育**: 新しい品質基準の理解と浸透
4. **ツール改善**: 自動化による人的エラーの削減