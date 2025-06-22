# 02_CLAUDE.mdルール違反

## 問題概要
CLAUDE.mdで定義されたルールに違反するコードが検出されています。

## None引数初期値（27件）
**ルール**: 引数にデフォルト値を指定するのを禁止する。呼び出し元で値を用意することを徹底する。

### 主な該当箇所
- `scripts/e2e.py:28` - `__init__`メソッド（3件）
- `scripts/infrastructure/command_executor.py` - 複数のメソッド（18件）
- `scripts/quality/check_generic_names.py:166` - `main`関数
- `scripts/quality/common.py:112` - `find_python_files`関数
- `scripts/quality_checks/base/base_quality_checker.py:29` - `get_target_files`メソッド

## フォールバック処理（12件）
**ルール**: フォールバック処理は禁止、必要なエラーを見逃すことになる。

### 主な該当箇所
- `scripts/infrastructure/command_executor.py:220` - `returncode = -1`
- `scripts/infrastructure/command_executor.py:165` - `return False`
- `scripts/quality/check_generic_names.py:164` - エラー時のフォールバック
- `scripts/quality/common.py:104` - try-except内でのフォールバック
- `scripts/quality/convert_dict_get.py` - 複数箇所でのフォールバック処理

## dict.get()使用（4件）
**ルール**: デフォルト値の使用をグローバルに禁止します。

### 該当箇所
- `scripts/quality/common.py:76` - `severity_symbol`
- `scripts/quality_checks/base/quality_config_loader.py:33` - excluded_directories
- `scripts/quality_checks/base/quality_config_loader.py:41` - script_paths
- `scripts/quality_checks/base/quality_config_loader.py:48` - allowed_directories

## print使用（119件）
**ルール**: 副作用はsrc/infrastructure tests/infrastructureのみとする、また、すべてmain.pyから注入する

### 主な該当箇所
- `scripts/analysis/analyze_architecture.py` - 複数箇所
- `scripts/infrastructure/logger.py` - print関数の定義・使用
- その他多数のファイルでの直接print使用

## 修正方針
1. None引数初期値 → 呼び出し元で明示的な値を設定
2. フォールバック処理 → 適切なエラーハンドリングに変更
3. dict.get() → 設定システムを通じた値取得に変更
4. print使用 → ログシステムの活用