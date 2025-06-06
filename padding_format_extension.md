# パディング・固定文字数フォーマット機能の拡張

## 🎯 機能概要

`str.zfill()` や `str.ljust()` のような固定文字数でのパディング機能をテスト結果フォーマッタに追加します。これにより、整列された見やすい出力が可能になります。

## 💡 実装例

### 1. 基本的なパディング機能

```python
# src/operations/formatters/padding_utils.py
from dataclasses import dataclass
from typing import Optional, Literal
from enum import Enum

class PaddingType(Enum):
    LEFT = "left"      # 左寄せ（右パディング）
    RIGHT = "right"    # 右寄せ（左パディング）
    CENTER = "center"  # 中央寄せ
    ZERO_FILL = "zfill" # ゼロパディング（数値用）

@dataclass(frozen=True)
class PaddingConfig:
    """パディング設定"""
    width: int                           # 固定文字数
    padding_type: PaddingType = PaddingType.LEFT  # パディングタイプ
    fill_char: str = ' '                # パディング文字（デフォルトはスペース）
    truncate: bool = True               # 長すぎる場合の切り詰め
    truncate_suffix: str = '...'        # 切り詰め時の末尾文字

class PaddingFormatter:
    """パディング処理のユーティリティクラス"""
    
    @staticmethod
    def format_with_padding(text: str, config: PaddingConfig) -> str:
        """指定された設定でパディングを適用"""
        # 切り詰め処理
        if config.truncate and len(text) > config.width:
            if config.width > len(config.truncate_suffix):
                truncated_width = config.width - len(config.truncate_suffix)
                text = text[:truncated_width] + config.truncate_suffix
            else:
                text = text[:config.width]
        
        # パディング処理
        if config.padding_type == PaddingType.LEFT:
            return text.ljust(config.width, config.fill_char)
        elif config.padding_type == PaddingType.RIGHT:
            return text.rjust(config.width, config.fill_char)
        elif config.padding_type == PaddingType.CENTER:
            return text.center(config.width, config.fill_char)
        elif config.padding_type == PaddingType.ZERO_FILL:
            # 数値のゼロパディング
            if text.isdigit():
                return text.zfill(config.width)
            else:
                # 数値でない場合は右寄せ
                return text.rjust(config.width, '0')
        else:
            return text
    
    @staticmethod
    def format_columns(items: List[str], configs: List[PaddingConfig], 
                      separator: str = ' | ') -> str:
        """複数カラムの整列フォーマット"""
        if len(items) != len(configs):
            raise ValueError("Items and configs must have the same length")
        
        formatted_items = []
        for item, config in zip(items, configs):
            formatted_items.append(PaddingFormatter.format_with_padding(item, config))
        
        return separator.join(formatted_items)
```

### 2. フォーマットオプションの拡張

```python
# src/operations/formatters/base_formatter.py (拡張版)
@dataclass(frozen=True)
class FormatOptions:
    """拡張されたフォーマットオプション"""
    format_type: str = "detailed"
    show_colors: bool = True
    show_timing: bool = False
    show_diff: bool = True
    max_output_lines: int = 10
    
    # パディング関連のオプション
    use_padding: bool = False
    test_name_width: Optional[int] = None      # テスト名の固定幅
    status_width: Optional[int] = None         # ステータスの固定幅
    time_width: Optional[int] = None          # 実行時間の固定幅
    padding_char: str = ' '                   # パディング文字
    column_separator: str = ' | '             # カラム区切り文字
    
    # 数値フォーマット
    time_format: str = "{:.3f}s"              # 時間表示フォーマット
    time_padding_type: str = "right"          # 時間のパディングタイプ
    
    custom_templates: Optional[Dict[str, str]] = None
    extra_options: Optional[Dict[str, Any]] = None
```

### 3. 表形式フォーマッタの実装

```python
# src/operations/formatters/table_formatter.py
class TableFormatter(TestResultFormatter):
    """表形式での整列フォーマッタ"""
    
    @property
    def name(self) -> str:
        return "table"
    
    def supports_format(self, format_type: str) -> bool:
        return format_type in ["table", "aligned"]
    
    def format_single_result(self, result: TestResult, options: FormatOptions) -> str:
        # デフォルトの幅設定
        test_name_width = options.test_name_width or 20
        status_width = options.status_width or 8
        time_width = options.time_width or 10
        
        # カラム設定
        test_name_config = PaddingConfig(
            width=test_name_width,
            padding_type=PaddingType.LEFT,
            fill_char=options.padding_char
        )
        
        status_config = PaddingConfig(
            width=status_width,
            padding_type=PaddingType.CENTER,
            fill_char=options.padding_char
        )
        
        time_config = PaddingConfig(
            width=time_width,
            padding_type=PaddingType.RIGHT if options.time_padding_type == "right" else PaddingType.LEFT,
            fill_char=options.padding_char
        )
        
        # データ準備
        test_name = result.test_name
        
        if result.status == TestStatus.PASS:
            status = "✓ PASS"
        elif result.status == TestStatus.FAIL:
            status = "✗ FAIL"
        elif result.status == TestStatus.ERROR:
            status = "✗ ERROR"
        else:
            status = "- SKIP"
        
        # 実行時間の整形
        if result.execution_time is not None and options.show_timing:
            time_str = options.time_format.format(result.execution_time)
        else:
            time_str = "-"
        
        # 表形式で整列
        columns = [test_name, status, time_str] if options.show_timing else [test_name, status]
        configs = [test_name_config, status_config, time_config] if options.show_timing else [test_name_config, status_config]
        
        return PaddingFormatter.format_columns(columns, configs, options.column_separator)
    
    def format_summary(self, results: List[TestResult], options: FormatOptions) -> str:
        total = len(results)
        passed = sum(1 for r in results if r.status == TestStatus.PASS)
        failed = sum(1 for r in results if r.status == TestStatus.FAIL)
        errors = sum(1 for r in results if r.status == TestStatus.ERROR)
        
        # サマリーも整列
        if options.use_padding:
            total_width = (options.test_name_width or 20) + (options.status_width or 8)
            if options.show_timing:
                total_width += (options.time_width or 10) + len(options.column_separator) * 2
            else:
                total_width += len(options.column_separator)
            
            separator = "=" * total_width
            summary = f"Tests: {passed} passed, {failed} failed, {errors} errors, {total} total"
            
            return f"{separator}\n{summary}"
        else:
            return f"Tests: {passed} passed, {failed} failed, {errors} errors, {total} total"
```

### 4. 数値パディング特化フォーマッタ

```python
# src/operations/formatters/numeric_formatter.py
class NumericFormatter(TestResultFormatter):
    """数値パディングに特化したフォーマッタ"""
    
    @property
    def name(self) -> str:
        return "numeric"
    
    def supports_format(self, format_type: str) -> bool:
        return format_type in ["numeric", "zfill"]
    
    def format_single_result(self, result: TestResult, options: FormatOptions) -> str:
        # テスト番号の抽出と0埋め
        test_number = self._extract_test_number(result.test_name)
        test_number_padded = str(test_number).zfill(options.test_name_width or 3)
        
        # ステータスの短縮形
        status_map = {
            TestStatus.PASS: "OK",
            TestStatus.FAIL: "NG", 
            TestStatus.ERROR: "ER",
            TestStatus.SKIP: "SK"
        }
        status = status_map.get(result.status, "??")
        
        # 実行時間の0埋め（ミリ秒単位）
        if result.execution_time is not None:
            time_ms = int(result.execution_time * 1000)
            time_padded = str(time_ms).zfill(options.time_width or 5)
            return f"[{test_number_padded}] {status} {time_padded}ms"
        else:
            return f"[{test_number_padded}] {status}"
    
    def _extract_test_number(self, test_name: str) -> int:
        """テスト名から番号を抽出"""
        import re
        match = re.search(r'(\d+)', test_name)
        return int(match.group(1)) if match else 0
    
    def format_summary(self, results: List[TestResult], options: FormatOptions) -> str:
        total = len(results)
        passed = sum(1 for r in results if r.status == TestStatus.PASS)
        
        # 数値も0埋め
        total_padded = str(total).zfill(3)
        passed_padded = str(passed).zfill(3)
        
        return f"Result: {passed_padded}/{total_padded}"
```

## 📝 env.json設定例

### 1. 基本的な表形式フォーマット

```json
{
  "python": {
    "commands": {
      "test_table": {
        "aliases": ["tt"],
        "description": "表形式でテスト結果を表示",
        "steps": [
          {
            "type": "test",
            "cmd": ["python3", "{workspace_path}/{source_file_name}"],
            "output_format": "table",
            "format_options": {
              "use_padding": true,
              "test_name_width": 25,
              "status_width": 10,
              "time_width": 12,
              "show_timing": true,
              "column_separator": " │ ",
              "padding_char": " "
            }
          }
        ]
      }
    }
  }
}
```

### 2. 数値0埋めフォーマット

```json
{
  "python": {
    "commands": {
      "test_numeric": {
        "aliases": ["tn"],
        "description": "数値0埋めでテスト結果を表示",
        "steps": [
          {
            "type": "test",
            "cmd": ["python3", "{workspace_path}/{source_file_name}"],
            "output_format": "numeric",
            "format_options": {
              "test_name_width": 3,
              "time_width": 5,
              "show_timing": true,
              "time_padding_type": "right"
            }
          }
        ]
      }
    }
  }
}
```

### 3. カスタムパディング

```json
{
  "python": {
    "commands": {
      "test_custom": {
        "aliases": ["tc"],
        "description": "カスタムパディングでテスト結果を表示",
        "steps": [
          {
            "type": "test",
            "cmd": ["python3", "{workspace_path}/{source_file_name}"],
            "output_format": "table",
            "format_options": {
              "use_padding": true,
              "test_name_width": 30,
              "status_width": 15,
              "time_width": 10,
              "show_timing": true,
              "column_separator": " ┃ ",
              "padding_char": ".",
              "time_format": "{:.2f}sec",
              "time_padding_type": "right"
            }
          }
        ]
      }
    }
  }
}
```

## 🎨 出力例

### 1. 表形式フォーマット (table)

```
sample-1.in           │    ✓ PASS    │     0.023s
sample-2.in           │    ✗ FAIL    │     0.041s
sample-very-long-name.in │    ✗ ERROR   │     0.002s
===================================================
Tests: 1 passed, 1 failed, 1 error, 3 total
```

### 2. 数値0埋めフォーマット (numeric)

```
[001] OK 00023ms
[002] NG 00041ms
[003] ER 00002ms
Result: 001/003
```

### 3. カスタムパディング

```
sample-1.in..................... ┃    ✓ PASS     ┃   0.02sec
sample-2.in..................... ┃    ✗ FAIL     ┃   0.04sec
sample-very-long-name.in........ ┃    ✗ ERROR    ┃   0.00sec
================================================================
Tests: 1 passed, 1 failed, 1 error, 3 total
```

## 🔧 高度な機能

### 1. 動的幅調整

```python
class AdaptiveTableFormatter(TableFormatter):
    """テスト名の長さに応じて動的に幅を調整するフォーマッタ"""
    
    def _calculate_optimal_widths(self, results: List[TestResult], 
                                 options: FormatOptions) -> Tuple[int, int, int]:
        """最適な幅を計算"""
        max_test_name_length = max(len(r.test_name) for r in results) if results else 10
        
        # 最小幅と最大幅の制限
        test_name_width = max(
            options.test_name_width or 15,
            min(max_test_name_length + 2, 50)
        )
        
        status_width = options.status_width or 10
        time_width = options.time_width or 10
        
        return test_name_width, status_width, time_width
```

### 2. ボーダー付きテーブル

```python
class BorderedTableFormatter(TableFormatter):
    """ボーダー付きテーブルフォーマッタ"""
    
    def format_results_with_border(self, results: List[TestResult], 
                                  options: FormatOptions) -> str:
        lines = []
        
        # ヘッダー
        headers = ["Test Name", "Status", "Time"] if options.show_timing else ["Test Name", "Status"]
        header_line = self._format_header(headers, options)
        lines.append(header_line)
        lines.append(self._create_separator_line(options))
        
        # データ行
        for result in results:
            lines.append(self.format_single_result(result, options))
        
        # フッター
        lines.append(self._create_separator_line(options))
        lines.append(self.format_summary(results, options))
        
        return "\n".join(lines)
    
    def _create_separator_line(self, options: FormatOptions) -> str:
        """区切り線の生成"""
        total_width = (options.test_name_width or 20) + (options.status_width or 8)
        if options.show_timing:
            total_width += (options.time_width or 10)
        
        return "+" + "-" * (total_width + len(options.column_separator) * 2) + "+"
```

## 📊 実装コスト

| 機能 | 追加時間 | 複雑度 | ファイル数 |
|------|----------|--------|------------|
| 基本パディング機能 | 2-3h | 低 | 2 |
| 表形式フォーマッタ | 2-3h | 中 | 1 |
| 数値0埋めフォーマッタ | 1-2h | 低 | 1 |
| 動的幅調整 | 1-2h | 中 | 1 |
| ボーダー機能 | 1h | 低 | 1 |
| **合計** | **7-11h** | **中** | **6** |

## ✅ 利点

1. **視認性向上**: 整列された出力で結果が見やすい
2. **カスタマイズ性**: パディング文字、幅、配置を自由に設定
3. **既存機能との統合**: 他のフォーマッタとシームレスに併用
4. **数値処理**: テスト番号や実行時間の0埋め表示
5. **拡張性**: 新しいパディングタイプを簡単に追加可能

この機能により、ユーザーは`zfill`のような固定文字数フォーマットを含む、高度に整列されたテスト結果出力を実現できます。