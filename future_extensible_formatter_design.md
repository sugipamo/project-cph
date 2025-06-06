# 将来拡張に強いテスト結果フォーマッタ設計

## 🎯 設計目標

1. **将来の変更に強い**: 新しいフォーマット形式を容易に追加可能
2. **プラグイン可能**: 外部フォーマッタとの統合
3. **設定駆動**: env.jsonでの完全な制御
4. **後方互換性**: 既存の動作を破損させない
5. **テスタブル**: 単体テストが容易な設計

## 🏗️ アーキテクチャ設計

### 1. コア抽象化

```python
# src/operations/formatters/base_formatter.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from enum import Enum

class TestStatus(Enum):
    PASS = "pass"
    FAIL = "fail" 
    ERROR = "error"
    SKIP = "skip"

@dataclass(frozen=True)
class TestResult:
    """テスト結果の不変データ構造"""
    test_name: str
    status: TestStatus
    expected_output: Optional[str] = None
    actual_output: Optional[str] = None
    error_message: Optional[str] = None
    execution_time: Optional[float] = None
    test_file_path: Optional[str] = None

@dataclass(frozen=True)
class FormatOptions:
    """フォーマットオプションの不変データ構造"""
    format_type: str = "detailed"
    show_colors: bool = True
    show_timing: bool = False
    show_diff: bool = True
    max_output_lines: int = 10
    custom_templates: Optional[Dict[str, str]] = None
    extra_options: Optional[Dict[str, Any]] = None

class TestResultFormatter(ABC):
    """テスト結果フォーマッタの抽象基底クラス"""
    
    @abstractmethod
    def format_single_result(self, result: TestResult, options: FormatOptions) -> str:
        """単一テスト結果のフォーマット"""
        pass
    
    @abstractmethod
    def format_summary(self, results: List[TestResult], options: FormatOptions) -> str:
        """サマリーのフォーマット"""
        pass
    
    @abstractmethod
    def supports_format(self, format_type: str) -> bool:
        """このフォーマッタが対応する形式かチェック"""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """フォーマッタ名"""
        pass
```

### 2. 具象フォーマッタ実装

```python
# src/operations/formatters/detailed_formatter.py
class DetailedFormatter(TestResultFormatter):
    """詳細フォーマッタ（現在のデフォルト）"""
    
    @property
    def name(self) -> str:
        return "detailed"
    
    def supports_format(self, format_type: str) -> bool:
        return format_type in ["detailed", "default"]
    
    def format_single_result(self, result: TestResult, options: FormatOptions) -> str:
        lines = [f"Testing {result.test_name}"]
        
        if result.status == TestStatus.PASS:
            lines.append("✓ PASS")
        elif result.status == TestStatus.FAIL:
            lines.extend([
                "✗ FAIL",
                "Expected:",
                f"{result.expected_output}",
                "Got:",
                f"{result.actual_output}"
            ])
        elif result.status == TestStatus.ERROR:
            lines.extend([
                "✗ ERROR",
                "Program failed with error:",
                f"{result.error_message}"
            ])
        
        if options.show_timing and result.execution_time:
            lines.append(f"Execution time: {result.execution_time:.3f}s")
        
        return "\n".join(lines)
    
    def format_summary(self, results: List[TestResult], options: FormatOptions) -> str:
        total = len(results)
        passed = sum(1 for r in results if r.status == TestStatus.PASS)
        failed = sum(1 for r in results if r.status == TestStatus.FAIL)
        errors = sum(1 for r in results if r.status == TestStatus.ERROR)
        
        return f"Tests: {passed} passed, {failed} failed, {errors} errors, {total} total"

# src/operations/formatters/compact_formatter.py
class CompactFormatter(TestResultFormatter):
    """コンパクトフォーマッタ"""
    
    @property
    def name(self) -> str:
        return "compact"
    
    def supports_format(self, format_type: str) -> bool:
        return format_type == "compact"
    
    def format_single_result(self, result: TestResult, options: FormatOptions) -> str:
        status_symbols = {
            TestStatus.PASS: "✓",
            TestStatus.FAIL: "✗",
            TestStatus.ERROR: "E",
            TestStatus.SKIP: "-"
        }
        symbol = status_symbols.get(result.status, "?")
        return f"[{symbol}] {result.test_name}"
    
    def format_summary(self, results: List[TestResult], options: FormatOptions) -> str:
        status_counts = {}
        for result in results:
            status_counts[result.status] = status_counts.get(result.status, 0) + 1
        
        summary_parts = []
        for status, count in status_counts.items():
            summary_parts.append(f"{status.value}: {count}")
        
        return " | ".join(summary_parts)

# src/operations/formatters/json_formatter.py
import json

class JsonFormatter(TestResultFormatter):
    """JSON形式フォーマッタ"""
    
    @property
    def name(self) -> str:
        return "json"
    
    def supports_format(self, format_type: str) -> bool:
        return format_type == "json"
    
    def format_single_result(self, result: TestResult, options: FormatOptions) -> str:
        result_dict = {
            "test_name": result.test_name,
            "status": result.status.value,
            "expected_output": result.expected_output,
            "actual_output": result.actual_output,
            "error_message": result.error_message,
            "execution_time": result.execution_time
        }
        return json.dumps(result_dict, ensure_ascii=False, indent=2)
    
    def format_summary(self, results: List[TestResult], options: FormatOptions) -> str:
        summary = {
            "total_tests": len(results),
            "passed": sum(1 for r in results if r.status == TestStatus.PASS),
            "failed": sum(1 for r in results if r.status == TestStatus.FAIL),
            "errors": sum(1 for r in results if r.status == TestStatus.ERROR),
            "results": [
                {
                    "test_name": r.test_name,
                    "status": r.status.value,
                    "execution_time": r.execution_time
                } for r in results
            ]
        }
        return json.dumps(summary, ensure_ascii=False, indent=2)
```

### 3. フォーマッタファクトリー

```python
# src/operations/formatters/formatter_factory.py
from typing import List, Optional, Dict
from .base_formatter import TestResultFormatter, FormatOptions
from .detailed_formatter import DetailedFormatter
from .compact_formatter import CompactFormatter
from .json_formatter import JsonFormatter

class FormatterRegistry:
    """フォーマッタのレジストリ（プラグイン対応）"""
    
    def __init__(self):
        self._formatters: List[TestResultFormatter] = []
        self._register_default_formatters()
    
    def _register_default_formatters(self):
        """デフォルトフォーマッタの登録"""
        self.register(DetailedFormatter())
        self.register(CompactFormatter())
        self.register(JsonFormatter())
    
    def register(self, formatter: TestResultFormatter):
        """新しいフォーマッタの登録"""
        self._formatters.append(formatter)
    
    def get_formatter(self, format_type: str) -> Optional[TestResultFormatter]:
        """指定されたタイプのフォーマッタを取得"""
        for formatter in self._formatters:
            if formatter.supports_format(format_type):
                return formatter
        return None
    
    def list_available_formats(self) -> List[str]:
        """利用可能なフォーマット一覧"""
        formats = set()
        for formatter in self._formatters:
            # 各フォーマッタがサポートするフォーマット一覧を取得
            # 実装では各フォーマッタにサポートフォーマット一覧メソッドを追加
            pass
        return list(formats)

class FormatterFactory:
    """フォーマッタ生成ファクトリー"""
    
    def __init__(self):
        self.registry = FormatterRegistry()
    
    def create_formatter(self, options: FormatOptions) -> TestResultFormatter:
        """設定に基づいてフォーマッタを生成"""
        formatter = self.registry.get_formatter(options.format_type)
        if formatter is None:
            # フォールバック: デフォルトフォーマッタ
            formatter = self.registry.get_formatter("detailed")
        return formatter
    
    def register_plugin_formatter(self, formatter: TestResultFormatter):
        """プラグインフォーマッタの登録"""
        self.registry.register(formatter)
```

### 4. テスト実行エンジンとの統合

```python
# src/operations/formatters/test_executor.py
from typing import List
from .base_formatter import TestResult, TestStatus, FormatOptions
from .formatter_factory import FormatterFactory

class TestExecutor:
    """テスト実行とフォーマットを統合するクラス"""
    
    def __init__(self, formatter_factory: FormatterFactory):
        self.formatter_factory = formatter_factory
    
    def execute_tests_with_formatting(self, 
                                    test_command: List[str],
                                    test_files: List[str],
                                    format_options: FormatOptions) -> str:
        """テストを実行して結果をフォーマット"""
        
        # 1. テストを実行してTestResultオブジェクトを生成
        results = self._execute_tests(test_command, test_files)
        
        # 2. フォーマッタを取得
        formatter = self.formatter_factory.create_formatter(format_options)
        
        # 3. 結果をフォーマット
        formatted_results = []
        for result in results:
            formatted_result = formatter.format_single_result(result, format_options)
            formatted_results.append(formatted_result)
        
        # 4. サマリーを追加
        summary = formatter.format_summary(results, format_options)
        
        return "\n".join(formatted_results + [summary])
    
    def _execute_tests(self, test_command: List[str], test_files: List[str]) -> List[TestResult]:
        """実際のテスト実行（既存のロジックを移植）"""
        results = []
        for test_file in test_files:
            # 既存のテスト実行ロジック
            result = self._run_single_test(test_command, test_file)
            results.append(result)
        return results
    
    def _run_single_test(self, command: List[str], test_file: str) -> TestResult:
        """単一テストの実行"""
        # 既存の実装を移植
        pass
```

### 5. 設定統合とenv.json連携

```python
# src/operations/formatters/config_integration.py
from typing import Dict, Any
from .base_formatter import FormatOptions

class FormatConfigResolver:
    """env.jsonからフォーマット設定を解決"""
    
    @staticmethod
    def resolve_format_options(step_config: Dict[str, Any], 
                             default_options: FormatOptions = None) -> FormatOptions:
        """step設定からFormatOptionsを生成"""
        
        # デフォルト設定
        base_options = default_options or FormatOptions()
        
        # step設定から上書き
        format_type = step_config.get("output_format", base_options.format_type)
        
        format_options_config = step_config.get("format_options", {})
        
        return FormatOptions(
            format_type=format_type,
            show_colors=format_options_config.get("show_colors", base_options.show_colors),
            show_timing=format_options_config.get("show_timing", base_options.show_timing),
            show_diff=format_options_config.get("show_diff", base_options.show_diff),
            max_output_lines=format_options_config.get("max_output_lines", base_options.max_output_lines),
            custom_templates=format_options_config.get("custom_templates"),
            extra_options=format_options_config.get("extra_options")
        )
```

### 6. 既存コードとの統合

```python
# src/operations/factory/unified_request_factory.py (修正版)
class ComplexRequestStrategy(RequestCreationStrategy):
    """Strategy for creating complex requests (TEST, BUILD, OJ)"""
    
    def create_request(self, step: Step, context: Any, env_manager: EnvironmentManager) -> Optional[BaseRequest]:
        if step.type == StepType.TEST:
            from src.operations.formatters.config_integration import FormatConfigResolver
            from src.operations.formatters.formatter_factory import FormatterFactory
            from src.operations.formatters.test_executor import TestExecutor
            
            # フォーマット設定を解決
            step_dict = step.__dict__ if hasattr(step, '__dict__') else {}
            format_options = FormatConfigResolver.resolve_format_options(step_dict)
            
            # 新しいテストエグゼキューターを使用
            formatter_factory = FormatterFactory()
            test_executor = TestExecutor(formatter_factory)
            
            # フォーマット対応のテストスクリプト生成
            formatted_cmd = self._format_step_values(step.cmd, context)
            contest_current_path = self._format_value('{contest_current_path}', context)
            
            # TestExecutorを使用した新しい実装
            test_script = test_executor.generate_test_script(
                command=formatted_cmd,
                test_directory=f"{contest_current_path}/test",
                format_options=format_options
            )
            
            return ShellRequest(
                cmd=['bash', '-c', test_script],
                timeout=env_manager.get_timeout(),
                cwd=self._format_value(step.cwd, context) if step.cwd else env_manager.get_working_directory(),
                env=getattr(step, 'env', None),
                allow_failure=getattr(step, 'allow_failure', False)
            )
```

## 📝 env.json設定例

```json
{
  "python": {
    "commands": {
      "test": {
        "aliases": ["t"],
        "description": "テストを実行する（フォーマット対応）",
        "steps": [
          {
            "type": "copy",
            "allow_failure": false,
            "show_output": false,
            "cmd": ["{contest_current_path}/{source_file_name}", "{workspace_path}/{source_file_name}"]
          },
          {
            "type": "test",
            "allow_failure": true,
            "show_output": true,
            "cmd": ["python3", "{workspace_path}/{source_file_name}"],
            "output_format": "detailed",
            "format_options": {
              "show_colors": true,
              "show_timing": true,
              "show_diff": true,
              "max_output_lines": 20,
              "custom_templates": {
                "pass": "✅ {test_name} - PASSED",
                "fail": "❌ {test_name} - FAILED",
                "error": "💥 {test_name} - ERROR"
              }
            }
          }
        ]
      },
      "test_compact": {
        "aliases": ["tc"],
        "description": "コンパクト形式でテスト実行",
        "steps": [
          {
            "type": "copy",
            "allow_failure": false,
            "show_output": false,
            "cmd": ["{contest_current_path}/{source_file_name}", "{workspace_path}/{source_file_name}"]
          },
          {
            "type": "test",
            "allow_failure": true,
            "show_output": true,
            "cmd": ["python3", "{workspace_path}/{source_file_name}"],
            "output_format": "compact"
          }
        ]
      },
      "test_json": {
        "aliases": ["tj"],
        "description": "JSON形式でテスト結果出力",
        "steps": [
          {
            "type": "copy",
            "allow_failure": false,
            "show_output": false,
            "cmd": ["{contest_current_path}/{source_file_name}", "{workspace_path}/{source_file_name}"]
          },
          {
            "type": "test",
            "allow_failure": true,
            "show_output": true,
            "cmd": ["python3", "{workspace_path}/{source_file_name}"],
            "output_format": "json",
            "format_options": {
              "show_timing": true
            }
          }
        ]
      }
    }
  }
}
```

## 🚀 プラグイン拡張例

```python
# プラグインフォーマッタの例
class CustomMarkdownFormatter(TestResultFormatter):
    """Markdownレポート形式のカスタムフォーマッタ"""
    
    @property
    def name(self) -> str:
        return "markdown"
    
    def supports_format(self, format_type: str) -> bool:
        return format_type == "markdown"
    
    def format_single_result(self, result: TestResult, options: FormatOptions) -> str:
        if result.status == TestStatus.PASS:
            return f"- ✅ **{result.test_name}**: PASSED"
        elif result.status == TestStatus.FAIL:
            return f"""- ❌ **{result.test_name}**: FAILED
  - Expected: `{result.expected_output}`
  - Got: `{result.actual_output}`"""
        else:
            return f"- 💥 **{result.test_name}**: ERROR - {result.error_message}"
    
    def format_summary(self, results: List[TestResult], options: FormatOptions) -> str:
        total = len(results)
        passed = sum(1 for r in results if r.status == TestStatus.PASS)
        return f"## Test Summary\n\n**Results**: {passed}/{total} tests passed"

# プラグインの登録
def register_custom_formatters(factory: FormatterFactory):
    factory.register_plugin_formatter(CustomMarkdownFormatter())
```

## 📊 実装コスト見積もり（将来拡張対応版）

| コンポーネント | ファイル数 | 推定時間 | 複雑度 |
|----------------|------------|----------|--------|
| コア抽象化 | 1 | 2-3h | 中 |
| 基本フォーマッタ3種 | 3 | 4-5h | 低-中 |
| ファクトリー・レジストリ | 2 | 2-3h | 中 |
| 設定統合 | 1 | 2h | 中 |
| 既存コード統合 | 1 | 3-4h | 高 |
| テスト作成 | 5 | 4-5h | 中 |
| **合計** | **13** | **17-22h** | **中-高** |

## 🎯 段階的実装プラン

### Phase 1 (6-8h): 基盤構築
1. 抽象化レイヤー作成
2. デフォルトフォーマッタ実装
3. 基本的なファクトリー

### Phase 2 (6-8h): 統合
1. 既存コードとの統合
2. env.json設定対応
3. 基本テスト作成

### Phase 3 (5-6h): 拡張機能
1. プラグインシステム
2. カスタムフォーマッタ例
3. 包括的テスト

## ✅ この設計の利点

1. **プラグイン可能**: 新しいフォーマッタを簡単に追加
2. **設定駆動**: env.jsonでの完全な制御
3. **テスタブル**: 純粋関数とDIによる高いテスタビリティ
4. **一貫性**: 既存のStrategyパターンに準拠
5. **段階的移行**: 既存機能を壊さずに導入可能
6. **将来拡張性**: 新しい要件への柔軟な対応