# 02_CLAUDE.mdルール違反

## 概要
CLAUDE.mdで定められたプロジェクトルールに違反する問題群

## 検出された問題

### None引数初期値使用（禁止ルール違反）
- **場所**:
  - `scripts/infrastructure/command_executor.py:256` - `def run`
  - `scripts/infrastructure/command_executor.py:309` - `def run_with_live_output`
  - `scripts/quality/functional_quality_check.py:294` - `def main`
  - `scripts/test_runner/test_runner.py:17` - `def __init__`

### フォールバック処理使用（禁止ルール違反）
- **場所**:
  - `scripts/analysis/analyze_architecture.py:359` - `return str(file_path)`
  - `scripts/infrastructure/command_executor.py:220` - `returncode = -1`
  - `scripts/quality/architecture_quality_check.py:61` - `return [], []`
  - `scripts/quality/convert_dict_get.py:109,111` - 複数のフォールバック
  - `scripts/quality/functional_quality_check.py:285,204` - 複数のフォールバック
  - その他多数

### dict.get()使用（禁止ルール違反）
- **問題**: エラー隠蔽防止・フォールバック対応禁止のため使用禁止
- **場所**: `scripts/quality/quality_utils.py:76`
- **状況**: 自動変換実行後も残存

## 修正要求
- 呼び出し元での適切な値準備の徹底
- フォールバック処理の完全排除
- dict.get()の完全置換