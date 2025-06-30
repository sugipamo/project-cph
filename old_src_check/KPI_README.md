# KPI Scoring System for src_check

## Overview

The KPI (Key Performance Indicator) scoring system is now the standard feature of src_check. It provides numerical quality scores for your Python code, analyzing code quality, architecture quality, and test quality to produce a comprehensive score from 0-100.

## Features

### Phase 1 (Implemented)
- ✅ KPI scoring model with three categories
- ✅ Scoring engine that converts check results to scores
- ✅ Backward compatibility layer
- ✅ CLI integration with flags
- ✅ Multiple output formats (text, JSON, markdown)
- ✅ Configuration file support
- ✅ Unit tests

### Phase 2 (Planned)
- 🔄 SQLite database for history tracking
- 🔄 Trend analysis and reporting
- 🔄 Pattern detection
- 🔄 Parallel execution mode
- 🔄 Web dashboard

## Usage

### Basic Usage
```bash
# Run src_check - KPI scoring is now automatic
python -m src_check

# KPI results are automatically saved to:
# - check_result/kpi_score.txt (human-readable format)
# - check_result/kpi_score.json (machine-readable format)
```

### Configuration Options
```bash
# Use custom KPI configuration
python -m src_check --config my_kpi_config.yaml

# Check specific paths
python -m src_check src/ tests/
```

### KPI専用エントリーポイント（詳細制御用）
```bash
# JSONフォーマットで出力
python -m src_check.kpi_main --format json --output report.json

# スコアが閾値を下回った場合に失敗
python -m src_check.kpi_main --threshold 70

# Markdownフォーマットで出力
python -m src_check.kpi_main --format markdown
```

## Scoring System

### Score Calculation
- **Base Score**: 50 points (configurable)
- **Range**: 0-100 points
- **Target**: 30-80 points

### Categories (Equal Weight)
1. **Code Quality** (33.3%)
   - Syntax errors
   - Code style issues
   - Complexity problems
   - Documentation gaps

2. **Architecture Quality** (33.3%)
   - Circular dependencies
   - Import issues
   - Layer violations
   - Module structure

3. **Test Quality** (33.4%)
   - Test coverage
   - Mock usage
   - Testability issues
   - Test naming

### Severity Impacts
- **Critical**: -10 points
- **High**: -5 points
- **Medium**: -3 points
- **Low**: -1 point
- **Info**: -0.5 points

## Configuration

Create `.src_check_kpi.yaml`:

```yaml
# Base score (starting point)
base_score: 50.0

# Category weights (must sum to 1.0)
weights:
  code_quality: 0.333
  architecture_quality: 0.333
  test_quality: 0.334

# Severity impacts
severity_impacts:
  critical: -10.0
  high: -5.0
  medium: -3.0
  low: -1.0
  info: -0.5
```

## Output Examples

### 標準出力（コンソール）
```
============================================================
📊 KPIスコア評価結果
============================================================
総合スコア: 72.3/100
  - コード品質:         24.1 (15 件)
  - アーキテクチャ品質: 28.5 (3 件)
  - テスト品質:         19.7 (8 件)

✅ 良好: コード品質は良好なレベルです。

詳細なKPIレポート: check_result/kpi_score.txt
JSON形式のレポート: check_result/kpi_score.json
```

### Text Format (kpi_score.txt)
```
================================================================================
KPI Score Report - Total Score: 72.3/100
================================================================================

Category Breakdown:
  Code Quality:         24.1 (15 issues)
  Architecture Quality: 28.5 (3 issues)
  Test Quality:         19.7 (8 issues)

Issue Summary:
  Critical: 0
  High:     2
  Medium:   10
  Low:      14
```

### JSON Format
```json
{
  "total_score": 72.3,
  "timestamp": "2024-01-01T10:00:00",
  "categories": {
    "code_quality": {
      "score": 24.1,
      "issues": 15
    },
    "architecture_quality": {
      "score": 28.5,
      "issues": 3
    },
    "test_quality": {
      "score": 19.7,
      "issues": 8
    }
  }
}
```

## 評価レベル

src_checkは以下の5段階でコード品質を評価します：

- 🎉 **優秀** (80点以上): コード品質が非常に高いレベルです！
- ✅ **良好** (70-79点): コード品質は良好なレベルです。
- 📈 **標準** (50-69点): コード品質は標準的なレベルです。改善の余地があります。
- ⚠️  **要改善** (30-49点): コード品質に問題があります。リファクタリングを検討してください。
- ❌ **危険** (30点未満): コード品質が非常に低いです。早急な対応が必要です。

## CI/CD Integration

```bash
# CIパイプラインでの使用例
python -m src_check

# または閾値を設定して品質チェック
python -m src_check.kpi_main --threshold 70 --format json --output kpi_report.json

# Exit codeで判定
if [ $? -ne 0 ]; then
  echo "Code quality below threshold"
  exit 1
fi
```

## Roadmap

### Phase 1 ✅ (Current)
- Core scoring engine
- Backward compatibility
- Basic CLI integration

### Phase 2 🔄 (Next)
- Database storage
- Historical tracking
- Trend analysis

### Phase 3 📋 (Future)
- Auto-improvement agents
- Web dashboard
- IDE integration

### Phase 4 📋 (Future)
- Machine learning optimization
- Custom rule creation
- Enterprise features