# 既存フォーマット構文の統合・応用

## 🎯 活用可能な既存フォーマット構文

### 1. Python str.format() / f-string 構文

#### 基本構文
```python
# Python f-string / str.format() の構文を活用
"{test_name:.<20} | {status:^10} | {time:>8.3f}s"
#  ^^^^^^^^^^^     ^^^^^^^^^^     ^^^^^^^^^^
#  左寄せ20文字     中央寄せ10文字   右寄せ8文字(小数点3桁)
#  ドットで埋める   

# 実際の例
"sample-1.in........ |   ✓ PASS   |    0.023s"
```

#### 応用例
```python
# env.json での設定例
{
  "format_templates": {
    "single_result": "{test_name:.<25} │ {status:^12} │ {time:>10.3f}s",
    "summary": "Results: {passed:03d}/{total:03d} tests passed",
    "error_detail": "  ❌ Expected: {expected}\n  ❌ Got:      {actual}"
  }
}
```

### 2. printf スタイル構文

#### C/Shell printf 構文
```bash
# printf 構文を活用
"%-20s | %10s | %8.3fs"
# ^^^^^^   ^^^^^^   ^^^^^^^
# 左寄せ20文字 中央10文字 右寄せ8文字小数点3桁

# env.json での設定例
{
  "format_templates": {
    "single_result": "%-25s │ %^12s │ %8.3fs",
    "test_number": "[%03d]",  # ゼロ埋め3桁
    "time_ms": "%05dms"       # ミリ秒のゼロ埋め5桁
  }
}
```

### 3. Rust/Golang fmt 構文

#### Rust format! マクロ構文
```rust
// Rust format! 構文の応用
"{name:.<width$} | {status:^10} | {time:>8.precision$}"

// env.json での応用
{
  "format_templates": {
    "result": "{test_name:.<{name_width}} │ {status:^{status_width}} │ {time:>{time_width}.3}s",
    "dynamic_widths": {
      "name_width": 25,
      "status_width": 12,
      "time_width": 10
    }
  }
}
```

### 4. Jinja2 テンプレート構文

#### Jinja2 フィルターとフォーマット
```jinja2
{# Jinja2 構文をベースにした高度なテンプレート #}
{{ test_name | ljust(25, '.') }} │ {{ status | center(12) }} │ {{ time | round(3) | rjust(10) }}s

{# 条件分岐とループ #}
{% for result in results %}
  {% if result.status == 'PASS' %}
    ✅ {{ result.test_name | ljust(20) }}
  {% elif result.status == 'FAIL' %}
    ❌ {{ result.test_name | ljust(20) }} - Expected: {{ result.expected }}
  {% endif %}
{% endfor %}
```

### 5. Markdown Table 構文

#### GitHub Flavored Markdown
```markdown
# Markdown テーブル形式での出力
| Test Name        | Status | Time     |
|:----------------|:------:|---------:|
| sample-1.in     | ✓ PASS |   0.023s |
| sample-2.in     | ✗ FAIL |   0.041s |
| very-long.in    | ✗ ERROR|   0.002s |
```

## 🏗️ 統合実装アーキテクチャ

### 1. マルチ構文パーサー

```python
# src/operations/formatters/syntax_parser.py
from abc import ABC, abstractmethod
from typing import Dict, Any, List
import re
from enum import Enum

class FormatSyntaxType(Enum):
    PYTHON_FORMAT = "python"     # "{name:.<20}"
    PRINTF = "printf"            # "%-20s"
    RUST_FORMAT = "rust"         # "{name:.<width$}"
    JINJA2 = "jinja2"           # "{{ name | ljust(20, '.') }}"
    MARKDOWN = "markdown"        # "| name | status |"

class FormatSyntaxParser(ABC):
    """フォーマット構文パーサーの抽象基底クラス"""
    
    @abstractmethod
    def parse(self, template: str, data: Dict[str, Any]) -> str:
        """テンプレートをパースして文字列を生成"""
        pass
    
    @abstractmethod
    def supports_syntax(self, template: str) -> bool:
        """この構文をサポートするかチェック"""
        pass

class PythonFormatParser(FormatSyntaxParser):
    """Python f-string/str.format() 構文パーサー"""
    
    def supports_syntax(self, template: str) -> bool:
        # Python format構文の検出: {name:format_spec}
        return bool(re.search(r'\{[^}]*:[^}]*\}', template))
    
    def parse(self, template: str, data: Dict[str, Any]) -> str:
        try:
            return template.format(**data)
        except (KeyError, ValueError) as e:
            return f"[Format Error: {e}]"

class PrintfFormatParser(FormatSyntaxParser):
    """printf スタイル構文パーサー"""
    
    def supports_syntax(self, template: str) -> bool:
        # printf構文の検出: %[flags][width][.precision][length]specifier
        return bool(re.search(r'%[-+0 #]*\*?[0-9]*\.?\*?[0-9]*[hlL]?[diouxXeEfFgGaAcspn%]', template))
    
    def parse(self, template: str, data: Dict[str, Any]) -> str:
        try:
            # printf構文をPythonのformat構文に変換
            converted_template = self._convert_printf_to_python(template)
            return converted_template.format(**data)
        except Exception as e:
            return f"[Printf Format Error: {e}]"
    
    def _convert_printf_to_python(self, printf_template: str) -> str:
        """printf構文をPythonのformat構文に変換"""
        # 簡略化された変換例
        # %-20s -> {value:<20}
        # %10s -> {value:>10}
        # %03d -> {value:03d}
        conversions = {
            r'%-(\d+)s': r'{value:<\1}',
            r'%(\d+)s': r'{value:>\1}',
            r'%0(\d+)d': r'{value:0\1d}',
            r'%\.(\d+)f': r'{value:.\1f}',
        }
        
        converted = printf_template
        for pattern, replacement in conversions.items():
            converted = re.sub(pattern, replacement, converted)
        
        return converted

class Jinja2FormatParser(FormatSyntaxParser):
    """Jinja2 テンプレート構文パーサー"""
    
    def supports_syntax(self, template: str) -> bool:
        # Jinja2構文の検出: {{ variable }} or {% control %}
        return bool(re.search(r'\{\{.*?\}\}|\{%.*?%\}', template))
    
    def parse(self, template: str, data: Dict[str, Any]) -> str:
        try:
            # 実際のJinja2エンジンを使用
            from jinja2 import Template
            jinja_template = Template(template)
            return jinja_template.render(**data)
        except ImportError:
            # Jinja2が利用できない場合の簡易実装
            return self._simple_jinja_parse(template, data)
        except Exception as e:
            return f"[Jinja2 Error: {e}]"
    
    def _simple_jinja_parse(self, template: str, data: Dict[str, Any]) -> str:
        """簡易Jinja2パーサー（基本的な変数展開のみ）"""
        result = template
        for key, value in data.items():
            result = result.replace(f"{{{{ {key} }}}}", str(value))
        return result

class MarkdownTableParser(FormatSyntaxParser):
    """Markdown テーブル構文パーサー"""
    
    def supports_syntax(self, template: str) -> bool:
        # Markdownテーブル構文の検出: | column | column |
        return bool(re.search(r'\|.*\|', template))
    
    def parse(self, template: str, data: Dict[str, Any]) -> str:
        # Markdownテーブルの生成
        return self._generate_markdown_table(data)
    
    def _generate_markdown_table(self, data: Dict[str, Any]) -> str:
        """Markdownテーブルの生成"""
        if 'results' in data:
            results = data['results']
            lines = []
            
            # ヘッダー
            lines.append("| Test Name | Status | Time |")
            lines.append("|:----------|:------:|-----:|")
            
            # データ行
            for result in results:
                status_emoji = "✅" if result['status'] == 'PASS' else "❌"
                time_str = f"{result.get('time', 0):.3f}s" if result.get('time') else "-"
                lines.append(f"| {result['test_name']} | {status_emoji} {result['status']} | {time_str} |")
            
            return "\n".join(lines)
        return "| No Data |"
```

### 2. 統一テンプレートエンジン

```python
# src/operations/formatters/template_engine.py
class UnifiedTemplateEngine:
    """複数のフォーマット構文を統一的に扱うエンジン"""
    
    def __init__(self):
        self.parsers = {
            FormatSyntaxType.PYTHON_FORMAT: PythonFormatParser(),
            FormatSyntaxType.PRINTF: PrintfFormatParser(),
            FormatSyntaxType.JINJA2: Jinja2FormatParser(),
            FormatSyntaxType.MARKDOWN: MarkdownTableParser(),
        }
        self.default_parser = self.parsers[FormatSyntaxType.PYTHON_FORMAT]
    
    def render(self, template: str, data: Dict[str, Any], 
              syntax_hint: Optional[FormatSyntaxType] = None) -> str:
        """テンプレートをレンダリング"""
        
        if syntax_hint and syntax_hint in self.parsers:
            # 明示的に構文が指定された場合
            parser = self.parsers[syntax_hint]
            return parser.parse(template, data)
        
        # 自動検出
        for parser in self.parsers.values():
            if parser.supports_syntax(template):
                return parser.parse(template, data)
        
        # デフォルトパーサーを使用
        return self.default_parser.parse(template, data)
    
    def register_parser(self, syntax_type: FormatSyntaxType, 
                       parser: FormatSyntaxParser):
        """新しいパーサーを登録"""
        self.parsers[syntax_type] = parser
```

### 3. 高度なフォーマッタ実装

```python
# src/operations/formatters/template_formatter.py
class TemplateFormatter(TestResultFormatter):
    """テンプレートベースの高機能フォーマッタ"""
    
    def __init__(self, templates: Dict[str, str], 
                 syntax_type: Optional[FormatSyntaxType] = None):
        self.templates = templates
        self.syntax_type = syntax_type
        self.engine = UnifiedTemplateEngine()
    
    @property
    def name(self) -> str:
        return "template"
    
    def supports_format(self, format_type: str) -> bool:
        return format_type in ["template", "custom", "advanced"]
    
    def format_single_result(self, result: TestResult, options: FormatOptions) -> str:
        # テンプレートデータの準備
        data = {
            'test_name': result.test_name,
            'status': result.status.value,
            'status_symbol': self._get_status_symbol(result.status),
            'expected_output': result.expected_output or '',
            'actual_output': result.actual_output or '',
            'error_message': result.error_message or '',
            'execution_time': result.execution_time or 0,
            'time_ms': int((result.execution_time or 0) * 1000),
        }
        
        # 動的な幅設定
        if hasattr(options, 'dynamic_widths'):
            data.update(options.dynamic_widths)
        
        # テンプレートの選択
        if result.status == TestStatus.PASS:
            template = self.templates.get('pass', self.templates.get('single_result', '{test_name} | {status}'))
        elif result.status == TestStatus.FAIL:
            template = self.templates.get('fail', self.templates.get('single_result', '{test_name} | {status}'))
        elif result.status == TestStatus.ERROR:
            template = self.templates.get('error', self.templates.get('single_result', '{test_name} | {status}'))
        else:
            template = self.templates.get('single_result', '{test_name} | {status}')
        
        return self.engine.render(template, data, self.syntax_type)
    
    def format_summary(self, results: List[TestResult], options: FormatOptions) -> str:
        # サマリーデータの準備
        total = len(results)
        passed = sum(1 for r in results if r.status == TestStatus.PASS)
        failed = sum(1 for r in results if r.status == TestStatus.FAIL)
        errors = sum(1 for r in results if r.status == TestStatus.ERROR)
        
        data = {
            'total': total,
            'passed': passed,
            'failed': failed,
            'errors': errors,
            'pass_rate': (passed / total * 100) if total > 0 else 0,
            'results': [self._result_to_dict(r) for r in results]
        }
        
        template = self.templates.get('summary', 'Tests: {passed}/{total} passed')
        return self.engine.render(template, data, self.syntax_type)
    
    def _get_status_symbol(self, status: TestStatus) -> str:
        symbols = {
            TestStatus.PASS: "✅",
            TestStatus.FAIL: "❌", 
            TestStatus.ERROR: "💥",
            TestStatus.SKIP: "⏭️"
        }
        return symbols.get(status, "❓")
    
    def _result_to_dict(self, result: TestResult) -> Dict[str, Any]:
        return {
            'test_name': result.test_name,
            'status': result.status.value,
            'time': result.execution_time,
            'expected': result.expected_output,
            'actual': result.actual_output,
            'error': result.error_message
        }
```

## 📝 env.json設定例

### 1. Python format構文

```json
{
  "python": {
    "commands": {
      "test_python_fmt": {
        "aliases": ["tpf"],
        "steps": [{
          "type": "test",
          "output_format": "template",
          "format_options": {
            "syntax_type": "python",
            "templates": {
              "single_result": "{test_name:.<30} │ {status_symbol} {status:^8} │ {execution_time:>8.3f}s",
              "pass": "{test_name:.<30} │ ✅ {status:^8} │ {execution_time:>8.3f}s",
              "fail": "{test_name:.<30} │ ❌ {status:^8} │ {execution_time:>8.3f}s\n    Expected: {expected_output}\n    Got:      {actual_output}",
              "summary": "Results: {passed:03d}/{total:03d} tests passed ({pass_rate:.1f}%)"
            }
          }
        }]
      }
    }
  }
}
```

### 2. printf構文

```json
{
  "python": {
    "commands": {
      "test_printf": {
        "aliases": ["tpr"],
        "steps": [{
          "type": "test", 
          "output_format": "template",
          "format_options": {
            "syntax_type": "printf",
            "templates": {
              "single_result": "%-25s | %10s | %8.3fs",
              "summary": "Results: %03d/%03d passed"
            }
          }
        }]
      }
    }
  }
}
```

### 3. Jinja2構文

```json
{
  "python": {
    "commands": {
      "test_jinja": {
        "aliases": ["tj2"],
        "steps": [{
          "type": "test",
          "output_format": "template", 
          "format_options": {
            "syntax_type": "jinja2",
            "templates": {
              "single_result": "{{ test_name | ljust(25, '.') }} │ {% if status == 'PASS' %}✅{% else %}❌{% endif %} {{ status | center(8) }} │ {{ execution_time | round(3) | rjust(8) }}s",
              "summary": "{% set total_tests = results | length %}{% set passed_tests = results | selectattr('status', 'equalto', 'PASS') | list | length %}✨ {{ passed_tests }}/{{ total_tests }} tests passed!"
            }
          }
        }]
      }
    }
  }
}
```

### 4. Markdown出力

```json
{
  "python": {
    "commands": {
      "test_markdown": {
        "aliases": ["tmd"],
        "steps": [{
          "type": "test",
          "output_format": "template",
          "format_options": {
            "syntax_type": "markdown",
            "templates": {
              "summary": "markdown_table"
            },
            "export_file": "test_results.md"
          }
        }]
      }
    }
  }
}
```

## 🎨 出力例

### Python format構文
```
sample-1.in................... │ ✅  PASS   │    0.023s
sample-2.in................... │ ❌  FAIL   │    0.041s
    Expected: 2
    Got:      1
sample-long-test-name.in...... │ ❌  FAIL   │    0.002s
Results: 001/003 tests passed (33.3%)
```

### Jinja2構文
```
sample-1.in................... │ ✅  PASS   │   0.023s
sample-2.in................... │ ❌  FAIL   │   0.041s
sample-long-test-name.in...... │ ❌  FAIL   │   0.002s
✨ 1/3 tests passed!
```

### Markdown出力
```markdown
| Test Name | Status | Time |
|:----------|:------:|-----:|
| sample-1.in | ✅ PASS | 0.023s |
| sample-2.in | ❌ FAIL | 0.041s |
| sample-long-test-name.in | ❌ FAIL | 0.002s |
```

## 📊 実装コスト

| 機能 | 時間 | 複雑度 | ファイル数 |
|------|------|--------|------------|
| 基本パーサー群 | 4-6h | 中 | 4 |
| 統一エンジン | 2-3h | 中 | 1 |
| テンプレートフォーマッタ | 3-4h | 中-高 | 1 |
| Jinja2統合 | 2-3h | 中 | 1 |
| **合計** | **11-16h** | **中-高** | **7** |

## ✅ 利点

1. **馴染みやすさ**: 既存の構文を活用でユーザーの学習コストが低い
2. **強力な表現力**: Jinja2などの本格的なテンプレートエンジンの活用
3. **段階的導入**: 既存のシンプルなフォーマットから高度なテンプレートまで
4. **エコシステム**: 既存のツールやライブラリとの連携
5. **拡張性**: 新しい構文パーサーを簡単に追加可能

この実装により、Python開発者にとって馴染み深い構文から、テンプレートエンジンの強力な機能まで、幅広いレベルでのカスタマイズが可能になります。

**総実装時間**: 基本フォーマッタ (17-22h) + パディング機能 (5-8h) + 構文統合 (11-16h) = **33-46時間**で、業界標準の構文を活用した非常に強力で使いやすいフォーマットシステムが構築できます。