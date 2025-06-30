# src_check KPI実装方針

## 1. 概要

src_checkをプロジェクトの品質指標（KPI）として機能させ、技術的負債の可視化と継続的な品質改善を実現する。

### 基本方針
- **スコアリング**: 50点スタートの加点減点方式（0-100点）
- **目標範囲**: 30-80点を維持
- **測定単位**: プロジェクト全体、ファイル/モジュール単位、関数単位
- **時系列追跡**: 全履歴をDBに保存し、パターンの再発を検知

## 2. 品質指標と配点

### 2.1 カテゴリと重み（初期値）
```json
{
  "weights": {
    "code_quality": 1.0,      // 33.3%
    "architecture_quality": 1.0,  // 33.3%
    "test_quality": 1.0       // 33.3%
  }
}
```

### 2.2 コード品質（基準点: 50点）

#### 測定項目と配点
| 項目 | 減点/加点 | 説明 |
|------|-----------|------|
| 不適切なtry-except | -5点/件 | `except Exception` や `except:` の使用 |
| デフォルト値の不適切使用 | -3点/件 | CLAUDE.md違反のデフォルト引数 |
| コード行数（ファイル） | -1点/100行超過 | 300行を超えるファイル |
| コード重複 | -2点/10行以上 | 10行以上の重複コード |
| 適切なエラーハンドリング | +2点/件 | Result型の使用など |

### 2.3 アーキテクチャ品質（基準点: 50点）

#### 測定項目と配点
| 項目 | 減点/加点 | 説明 |
|------|-----------|------|
| 循環依存 | -10点/件 | 循環インポートの検出 |
| レイヤー違反 | -5点/件 | アーキテクチャルールの違反 |
| 過度なインポート数 | -1点/10件超過 | 1ファイルのインポート数 |
| 依存の深さ | -2点/5階層超過 | 依存関係の階層深度 |
| 依存性注入の実装 | +3点/件 | 適切なDI実装 |

### 2.4 テスト品質（基準点: 50点）

#### 測定項目と配点
| 項目 | 減点/加点 | 説明 |
|------|-----------|------|
| テストカバレッジ不足 | -1点/5%不足 | 80%を基準とする |
| テスト容易性（引数過多） | -2点/件 | 5個以上の引数を持つ関数 |
| 副作用のある関数 | -3点/件 | テスト困難な副作用 |
| モックの過度な使用 | -1点/5個超過 | 1テストでのモック数 |
| 単体テストの充実度 | +2点/モジュール | 適切な単体テスト |

## 3. テスト容易性の詳細評価

### 3.1 評価基準
```python
def calculate_testability_score(function_ast):
    score = 50  # 基準点
    
    # 引数の数
    arg_count = len(function_ast.args.args)
    if arg_count > 5:
        score -= (arg_count - 5) * 2
    
    # 副作用の検出
    side_effects = detect_side_effects(function_ast)
    score -= len(side_effects) * 3
    
    # 依存性注入の評価
    if has_dependency_injection(function_ast):
        score += 3
    
    # モックの必要性
    mock_requirements = analyze_mock_requirements(function_ast)
    if len(mock_requirements) > 5:
        score -= (len(mock_requirements) - 5)
    
    return max(0, min(100, score))
```

## 4. 時系列変化の検知

### 4.1 データベーススキーマ
```sql
CREATE TABLE function_history (
    id INTEGER PRIMARY KEY,
    file_path TEXT NOT NULL,
    function_name TEXT NOT NULL,
    ast_hash TEXT NOT NULL,
    ast_vector TEXT NOT NULL,  -- JSON形式のベクトル
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    kpi_score REAL,
    code_quality_score REAL,
    architecture_quality_score REAL,
    test_quality_score REAL
);

CREATE TABLE pattern_detection (
    id INTEGER PRIMARY KEY,
    pattern_type TEXT NOT NULL,  -- 'reversion', 'resurrection', 'antipattern_recurrence'
    function_id INTEGER REFERENCES function_history(id),
    similar_function_id INTEGER REFERENCES function_history(id),
    similarity_score REAL,
    detected_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 4.2 類似度計算
```python
def calculate_similarity(ast1, ast2):
    # AST構造をベクトル化
    vector1 = ast_to_vector(ast1)
    vector2 = ast_to_vector(ast2)
    
    # コサイン類似度
    cosine_sim = cosine_similarity(vector1, vector2)
    
    # 関数名の編集距離（ハイブリッド）
    name_distance = levenshtein_distance(ast1.name, ast2.name)
    name_similarity = 1 - (name_distance / max(len(ast1.name), len(ast2.name)))
    
    # ハイブリッドスコア
    return 0.7 * cosine_sim + 0.3 * name_similarity
```

### 4.3 パターン検知
- **リファクタリング後の復帰**: 類似度90%以上で検出
- **削除コードの復活**: AST構造の完全一致
- **アンチパターンの再発**: 特定のパターンマッチング

## 5. 出力形式

### 5.1 JSON出力（スコアのみ）
```json
{
  "timestamp": "2024-06-30T12:00:00Z",
  "total_score": 65.5,
  "scores": {
    "code_quality": 68.0,
    "architecture_quality": 62.5,
    "test_quality": 66.0
  },
  "status": "normal",  // "excellent", "normal", "warning"
  "trend": "improving"  // "improving", "stable", "declining"
}
```

### 5.2 Markdown詳細レポート
```markdown
# KPI Report - 2024-06-30

## Executive Summary
- **Total Score**: 65.5/100 (Normal)
- **Trend**: Improving ↑
- **Key Issues**: 3 critical, 12 major, 45 minor

## Detailed Scores

### Code Quality: 68.0/100
- Inappropriate try-except: -15 (3 violations)
- Default arguments: -12 (4 violations)
- Code duplication: -4 (2 instances)
- [+] Good error handling: +9 (3 implementations)

### Architecture Quality: 62.5/100
[詳細な違反リスト]

### Test Quality: 66.0/100
[カバレッジ詳細、テスト容易性分析]

## Pattern Detection
- ⚠️ Antipattern recurrence detected in `src/utils/file_ops.py`
- ✓ No circular dependencies detected

## Recommendations
1. Priority 1: Fix circular dependency risks
2. Priority 2: Improve test coverage in core modules
3. Priority 3: Refactor large files
```

## 6. worktreeとビームサーチ戦略

### 6.1 エージェント構成
```yaml
beam_search_config:
  agents:
    - name: "agent_1"
      focus: "自動決定"  # 現在のKPIスコアから最も改善が必要な領域
      worktree: "improvement_1"
    - name: "agent_2"
      focus: "自動決定"
      worktree: "improvement_2"
    - name: "agent_3"
      focus: "自動決定"
      worktree: "improvement_3"
  
  coordinator:
    selection_criteria:
      - kpi_score_improvement: 0.7  # 重み
      - future_value: 0.3          # 将来性の評価
```

### 6.2 エージェント役割の動的割り当て
```python
def assign_agent_roles(current_kpi_scores):
    # 最も低いスコアのカテゴリを特定
    priorities = sorted(current_kpi_scores.items(), key=lambda x: x[1])
    
    # エージェントの割り当て
    if priorities[0][1] < 40:  # 危機的な領域がある場合
        return {
            "agent_1": priorities[0][0],  # 最低スコア領域
            "agent_2": priorities[0][0],  # 同じ領域に2エージェント
            "agent_3": priorities[1][0]   # 2番目に低い領域
        }
    else:  # バランス良く改善
        return {
            "agent_1": priorities[0][0],
            "agent_2": priorities[1][0],
            "agent_3": priorities[2][0]
        }
```

## 7. 設定ファイル

### 7.1 kpi_config.json
```json
{
  "scoring": {
    "base_score": 50,
    "min_score": 0,
    "max_score": 100,
    "warning_threshold": 30,
    "excellent_threshold": 80
  },
  "weights": {
    "code_quality": 1.0,
    "architecture_quality": 1.0,
    "test_quality": 1.0
  },
  "penalties": {
    "inappropriate_try_except": -5,
    "default_arguments": -3,
    "circular_dependency": -10,
    "layer_violation": -5,
    "low_coverage_per_5_percent": -1
  },
  "bonuses": {
    "proper_error_handling": 2,
    "dependency_injection": 3,
    "comprehensive_unit_tests": 2
  },
  "similarity_threshold": 0.9,
  "database": {
    "path": "kpi_history.db",
    "retention_days": null  // 全履歴保存
  }
}
```

## 8. 実装優先順位

1. **Phase 1** (1週間)
   - 基本的なスコアリングシステムの実装
   - JSON/Markdown出力機能

2. **Phase 2** (1週間)
   - データベース統合
   - 時系列追跡機能

3. **Phase 3** (1週間)
   - パターン検知システム
   - 類似度計算の実装

4. **Phase 4** (1週間)
   - worktree統合
   - エージェント自動割り当て

## 9. 成功指標

- プロジェクト全体のKPIスコアが30-80の範囲で安定
- 月次でのスコア改善率5%以上
- アンチパターンの再発率50%削減
- 開発者の品質意識向上（定性評価）