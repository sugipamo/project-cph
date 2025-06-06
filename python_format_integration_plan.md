# Python Format構文統合実装プラン

## 🎯 設計方針

既存のフォーマット処理基盤を**拡張**する方針で、Python format構文のみに焦点を当てつつ将来拡張可能な抽象化を実装します。

### 調査結果に基づく判断

1. **既存基盤の活用**: `src/context/utils/format_utils.py` の高品質な基盤を活用
2. **統合ライブラリとの連携**: `src/utils/formatting/` の機能拡張
3. **段階的拡張**: 置き換えではなく拡張による安全な機能追加

## 🏗️ アーキテクチャ設計

### 1. 抽象化レイヤー

```python
# src/operations/formatters/base_format_engine.py
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum

class FormatSyntaxType(Enum):
    """サポートするフォーマット構文タイプ"""
    PYTHON = "python"          # 現在実装: Python str.format()
    PRINTF = "printf"          # 将来拡張: printf style
    JINJA2 = "jinja2"         # 将来拡張: Jinja2
    TEMPLATE = "template"     # 将来拡張: カスタムテンプレート

@dataclass(frozen=True)
class FormatContext:
    """フォーマット処理のコンテキスト（不変）"""
    data: Dict[str, Any]
    syntax_type: FormatSyntaxType = FormatSyntaxType.PYTHON
    strict_mode: bool = True
    fallback_value: str = ""
    extra_options: Optional[Dict[str, Any]] = None

class FormatResult:
    """フォーマット結果（成功/失敗情報含む）"""
    
    def __init__(self, formatted_text: str, success: bool = True, 
                 missing_keys: Optional[List[str]] = None, 
                 error_message: Optional[str] = None):
        self.formatted_text = formatted_text
        self.success = success
        self.missing_keys = missing_keys or []
        self.error_message = error_message
    
    def __str__(self) -> str:
        return self.formatted_text
    
    @property
    def is_success(self) -> bool:
        return self.success

class FormatEngine(ABC):
    """フォーマットエンジンの抽象基底クラス"""
    
    @abstractmethod
    def supports_syntax(self, template: str) -> bool:
        """この構文をサポートするかチェック"""
        pass
    
    @abstractmethod
    def format(self, template: str, context: FormatContext) -> FormatResult:
        """テンプレートをフォーマット"""
        pass
    
    @property
    @abstractmethod
    def syntax_type(self) -> FormatSyntaxType:
        """サポートする構文タイプ"""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """エンジン名"""
        pass
```

### 2. Python Format エンジン実装

```python
# src/operations/formatters/python_format_engine.py
import re
import string
from typing import Dict, Any, List, Set
from src.context.utils.format_utils import format_with_missing_keys, extract_format_keys
from .base_format_engine import FormatEngine, FormatContext, FormatResult, FormatSyntaxType

class PythonFormatEngine(FormatEngine):
    """Python str.format() / f-string 構文エンジン"""
    
    # 高度なPython format仕様の検出パターン
    PYTHON_FORMAT_PATTERN = re.compile(
        r'\{[^}]*:[^}]*\}|'      # {name:format_spec}
        r'\{[^}]*\![^}]*\}|'     # {name!conversion}
        r'\{[0-9]+\}'            # {0}, {1} (positional)
    )
    
    @property
    def syntax_type(self) -> FormatSyntaxType:
        return FormatSyntaxType.PYTHON
    
    @property
    def name(self) -> str:
        return "python_format"
    
    def supports_syntax(self, template: str) -> bool:
        """Python format構文の検出"""
        # 基本的な{key}形式
        if extract_format_keys(template):
            return True
        
        # 高度なformat仕様: {name:format_spec}, {name!conversion}
        return bool(self.PYTHON_FORMAT_PATTERN.search(template))
    
    def format(self, template: str, context: FormatContext) -> FormatResult:
        """Python format構文でのフォーマット処理"""
        try:
            if self._has_advanced_format_spec(template):
                # 高度なformat仕様の処理
                return self._format_advanced(template, context)
            else:
                # 既存の基本処理を活用
                return self._format_basic(template, context)
        
        except Exception as e:
            return FormatResult(
                formatted_text=template,
                success=False,
                error_message=str(e)
            )
    
    def _has_advanced_format_spec(self, template: str) -> bool:
        """高度なformat仕様が含まれているかチェック"""
        return bool(self.PYTHON_FORMAT_PATTERN.search(template))
    
    def _format_basic(self, template: str, context: FormatContext) -> FormatResult:
        """基本的なフォーマット処理（既存機能活用）"""
        try:
            formatted, missing = format_with_missing_keys(template, **context.data)
            
            if missing and context.strict_mode:
                return FormatResult(
                    formatted_text=formatted,
                    success=False,
                    missing_keys=missing,
                    error_message=f"Missing keys: {missing}"
                )
            
            return FormatResult(formatted_text=formatted, missing_keys=missing)
        
        except Exception as e:
            return FormatResult(
                formatted_text=template,
                success=False,
                error_message=str(e)
            )
    
    def _format_advanced(self, template: str, context: FormatContext) -> FormatResult:
        """高度なformat仕様の処理"""
        try:
            # Python組み込みのstr.format()を使用
            formatted = template.format(**context.data)
            return FormatResult(formatted_text=formatted)
        
        except KeyError as e:
            missing_key = str(e).strip("'\"")
            if context.strict_mode:
                return FormatResult(
                    formatted_text=template,
                    success=False,
                    missing_keys=[missing_key],
                    error_message=f"Missing key: {missing_key}"
                )
            else:
                # フォールバック処理
                safe_data = self._create_safe_data(context.data, template)
                try:
                    formatted = template.format(**safe_data)
                    return FormatResult(
                        formatted_text=formatted,
                        missing_keys=[missing_key]
                    )
                except Exception:
                    return FormatResult(
                        formatted_text=template,
                        success=False,
                        missing_keys=[missing_key],
                        error_message=str(e)
                    )
        
        except (ValueError, TypeError) as e:
            return FormatResult(
                formatted_text=template,
                success=False,
                error_message=f"Format error: {e}"
            )
    
    def _create_safe_data(self, data: Dict[str, Any], template: str) -> Dict[str, Any]:
        """安全なデータ辞書の作成（欠損キー対応）"""
        safe_data = data.copy()
        
        # テンプレートから必要なキーを抽出
        required_keys = self._extract_all_format_keys(template)
        
        # 欠損キーにフォールバック値を設定
        for key in required_keys:
            if key not in safe_data:
                safe_data[key] = ""  # 空文字列でフォールバック
        
        return safe_data
    
    def _extract_all_format_keys(self, template: str) -> Set[str]:
        """テンプレートから全てのキーを抽出"""
        keys = set()
        
        # 基本的な{key}形式
        keys.update(extract_format_keys(template))
        
        # 高度なformat仕様から抽出
        for match in self.PYTHON_FORMAT_PATTERN.finditer(template):
            spec = match.group(0)
            # {name:format} or {name!conversion} からnameを抽出
            if ':' in spec:
                key = spec[1:].split(':')[0]
            elif '!' in spec:
                key = spec[1:].split('!')[0]
            else:
                key = spec[1:-1]
            
            if key and not key.isdigit():  # positional引数でない場合
                keys.add(key)
        
        return keys

class EnhancedPythonFormatEngine(PythonFormatEngine):
    """拡張Python formatエンジン（将来の高度な機能用）"""
    
    @property
    def name(self) -> str:
        return "enhanced_python_format"
    
    def _format_advanced(self, template: str, context: FormatContext) -> FormatResult:
        """拡張機能付きの高度なformat処理"""
        # カスタムフォーマッタの適用
        if context.extra_options and 'custom_formatters' in context.extra_options:
            return self._apply_custom_formatters(template, context)
        
        # 基本処理
        return super()._format_advanced(template, context)
    
    def _apply_custom_formatters(self, template: str, context: FormatContext) -> FormatResult:
        """カスタムフォーマッタの適用"""
        # 将来実装: カスタムフォーマット仕様の処理
        # 例: {time:ms} → ミリ秒表示, {size:human} → 人間可読サイズ
        return super()._format_advanced(template, context)
```

### 3. フォーマットマネージャー

```python
# src/operations/formatters/format_manager.py
from typing import Dict, List, Optional
from .base_format_engine import FormatEngine, FormatContext, FormatResult, FormatSyntaxType
from .python_format_engine import PythonFormatEngine, EnhancedPythonFormatEngine

class FormatManager:
    """フォーマットエンジンの統一管理"""
    
    def __init__(self):
        self._engines: Dict[FormatSyntaxType, FormatEngine] = {}
        self._default_engine: Optional[FormatEngine] = None
        self._register_default_engines()
    
    def _register_default_engines(self):
        """デフォルトエンジンの登録"""
        # Python formatエンジン
        python_engine = PythonFormatEngine()
        self.register_engine(python_engine)
        
        # 拡張Python formatエンジン
        enhanced_engine = EnhancedPythonFormatEngine()
        self.register_engine(enhanced_engine, is_default=True)
    
    def register_engine(self, engine: FormatEngine, is_default: bool = False):
        """新しいエンジンの登録"""
        self._engines[engine.syntax_type] = engine
        if is_default:
            self._default_engine = engine
    
    def format(self, template: str, data: Dict[str, Any], 
              syntax_type: Optional[FormatSyntaxType] = None,
              strict_mode: bool = True,
              **extra_options) -> FormatResult:
        """統一フォーマット処理"""
        
        # コンテキスト作成
        context = FormatContext(
            data=data,
            syntax_type=syntax_type or FormatSyntaxType.PYTHON,
            strict_mode=strict_mode,
            extra_options=extra_options if extra_options else None
        )
        
        # エンジンの選択
        if syntax_type and syntax_type in self._engines:
            engine = self._engines[syntax_type]
        else:
            # 自動検出
            engine = self._detect_engine(template)
        
        return engine.format(template, context)
    
    def _detect_engine(self, template: str) -> FormatEngine:
        """テンプレートに適したエンジンの自動検出"""
        for engine in self._engines.values():
            if engine.supports_syntax(template):
                return engine
        
        # フォールバック: デフォルトエンジン
        return self._default_engine or list(self._engines.values())[0]
    
    def get_supported_syntax_types(self) -> List[FormatSyntaxType]:
        """サポートされている構文タイプ一覧"""
        return list(self._engines.keys())
    
    def is_syntax_supported(self, syntax_type: FormatSyntaxType) -> bool:
        """指定された構文がサポートされているかチェック"""
        return syntax_type in self._engines

# グローバルインスタンス（シングルトン的使用）
_format_manager = FormatManager()

def get_format_manager() -> FormatManager:
    """フォーマットマネージャーのグローバルインスタンス取得"""
    return _format_manager

# 便利関数
def format_template(template: str, data: Dict[str, Any], **kwargs) -> FormatResult:
    """簡単なフォーマット処理関数"""
    return _format_manager.format(template, data, **kwargs)
```

### 4. テスト結果フォーマッタとの統合

```python
# src/operations/formatters/test_result_formatter.py (拡張版)
from typing import Dict, Any, Optional
from dataclasses import dataclass
from .base_format_engine import FormatSyntaxType
from .format_manager import get_format_manager
from ..base_formatter import TestResult, TestStatus, FormatOptions

@dataclass(frozen=True)
class AdvancedFormatOptions(FormatOptions):
    """拡張フォーマットオプション"""
    # 既存オプション継承
    
    # Python format構文関連
    template_syntax: FormatSyntaxType = FormatSyntaxType.PYTHON
    strict_formatting: bool = True
    custom_formatters: Optional[Dict[str, str]] = None
    
    # テンプレート定義
    templates: Optional[Dict[str, str]] = None

class TemplateBasedFormatter(TestResultFormatter):
    """テンプレートベースのテスト結果フォーマッタ"""
    
    def __init__(self, default_templates: Optional[Dict[str, str]] = None):
        self.format_manager = get_format_manager()
        self.default_templates = default_templates or self._get_default_templates()
    
    @property
    def name(self) -> str:
        return "template_based"
    
    def supports_format(self, format_type: str) -> bool:
        return format_type in ["template", "python_format", "advanced"]
    
    def format_single_result(self, result: TestResult, options: AdvancedFormatOptions) -> str:
        # テンプレートの選択
        template = self._select_template(result, options)
        
        # データの準備
        format_data = self._prepare_format_data(result, options)
        
        # フォーマット実行
        format_result = self.format_manager.format(
            template=template,
            data=format_data,
            syntax_type=options.template_syntax,
            strict_mode=options.strict_formatting
        )
        
        if not format_result.success and options.strict_formatting:
            # エラー時のフォールバック
            return f"[Format Error] {result.test_name}: {result.status.value}"
        
        return format_result.formatted_text
    
    def _select_template(self, result: TestResult, options: AdvancedFormatOptions) -> str:
        """結果に応じたテンプレートの選択"""
        templates = options.templates or self.default_templates
        
        # ステータス別テンプレート
        status_key = result.status.value.lower()
        if status_key in templates:
            return templates[status_key]
        
        # デフォルトテンプレート
        return templates.get('default', '{test_name} | {status}')
    
    def _prepare_format_data(self, result: TestResult, options: AdvancedFormatOptions) -> Dict[str, Any]:
        """フォーマット用データの準備"""
        data = {
            'test_name': result.test_name,
            'status': result.status.value,
            'status_upper': result.status.value.upper(),
            'status_symbol': self._get_status_symbol(result.status),
            'expected_output': result.expected_output or '',
            'actual_output': result.actual_output or '',
            'error_message': result.error_message or '',
            'execution_time': result.execution_time or 0.0,
            'time_ms': int((result.execution_time or 0) * 1000),
            'time_formatted': f"{result.execution_time:.3f}s" if result.execution_time else "-",
        }
        
        # カスタムフォーマッタの適用
        if options.custom_formatters:
            data.update(options.custom_formatters)
        
        return data
    
    def _get_status_symbol(self, status: TestStatus) -> str:
        """ステータスシンボルの取得"""
        symbols = {
            TestStatus.PASS: "✅",
            TestStatus.FAIL: "❌",
            TestStatus.ERROR: "💥",
            TestStatus.SKIP: "⏭️"
        }
        return symbols.get(status, "❓")
    
    def _get_default_templates(self) -> Dict[str, str]:
        """デフォルトテンプレートの定義"""
        return {
            'default': '{test_name:.<25} | {status_symbol} {status:^8} | {time_formatted:>10}',
            'pass': '{test_name:.<25} | {status_symbol} {status:^8} | {time_formatted:>10}',
            'fail': '{test_name:.<25} | {status_symbol} {status:^8} | {time_formatted:>10}\\n  Expected: {expected_output}\\n  Got:      {actual_output}',
            'error': '{test_name:.<25} | {status_symbol} {status:^8} | {time_formatted:>10}\\n  Error: {error_message}',
            'summary': 'Tests: {passed:03d}/{total:03d} passed ({pass_rate:.1f}%)'
        }
```

## 📝 env.json設定例

### 基本的なPython format構文

```json
{
  "python": {
    "commands": {
      "test_format": {
        "aliases": ["tf"],
        "description": "Python format構文でテスト結果表示",
        "steps": [
          {
            "type": "test",
            "cmd": ["python3", "{workspace_path}/{source_file_name}"],
            "output_format": "template",
            "format_options": {
              "template_syntax": "python",
              "strict_formatting": true,
              "templates": {
                "default": "{test_name:.<30} │ {status_symbol} {status:^10} │ {time_formatted:>12}",
                "pass": "{test_name:.<30} │ {status_symbol} {status:^10} │ {time_formatted:>12}",
                "fail": "{test_name:.<30} │ {status_symbol} {status:^10} │ {time_formatted:>12}\\n    Expected: {expected_output}\\n    Got:      {actual_output}",
                "summary": "Results: {passed:03d}/{total:03d} tests passed"
              }
            }
          }
        ]
      }
    }
  }
}
```

### 高度な数値フォーマット

```json
{
  "format_options": {
    "templates": {
      "default": "{test_name:.<25} | {status:^8} | {execution_time:>8.3f}s | {time_ms:>5d}ms",
      "summary": "Tests: {passed:03d}/{total:03d} passed ({pass_rate:>6.2f}%)"
    }
  }
}
```

## 🎨 出力例

### 基本出力
```
sample-1.in................... │ ✅   PASS    │       0.023s
sample-2.in................... │ ❌   FAIL    │       0.041s
    Expected: 2
    Got:      1
sample-long-test-name.in...... │ 💥  ERROR    │       0.002s
    Error: ValueError: invalid literal for int()
Results: 001/003 tests passed
```

### 数値フォーマット出力
```
sample-1.in........... |   PASS   |    0.023s |    23ms
sample-2.in........... |   FAIL   |    0.041s |    41ms
sample-3.in........... |  ERROR   |    0.002s |     2ms
Tests: 001/003 passed ( 33.33%)
```

## 📊 実装コスト

| コンポーネント | 時間 | 複雑度 | ファイル数 |
|---------------|------|--------|------------|
| 抽象化レイヤー | 2-3h | 中 | 1 |
| Python formatエンジン | 4-5h | 中-高 | 1 |
| フォーマットマネージャー | 2-3h | 中 | 1 |
| テスト結果フォーマッタ統合 | 3-4h | 中-高 | 1 |
| テスト作成 | 3-4h | 中 | 3 |
| **合計** | **14-19h** | **中-高** | **7** |

## ✅ 設計の利点

1. **既存基盤の活用**: `format_utils.py` の高品質な機能を継承
2. **段階的拡張**: 既存コードを破損させない安全な拡張
3. **将来拡張性**: 新しい構文エンジンを簡単に追加可能
4. **型安全性**: 不変データクラスによる安全な処理
5. **パフォーマンス**: 既存の最適化機能を継承

## 🔄 段階的実装プラン

### Phase 1: 基盤構築 (6-8h)
1. 抽象化レイヤーの実装
2. 基本Python formatエンジン
3. フォーマットマネージャー

### Phase 2: 統合とテスト (5-7h)
1. テスト結果フォーマッタ統合
2. env.json設定対応
3. 包括的テスト作成

### Phase 3: 最適化と文書化 (3-4h)
1. パフォーマンス最適化
2. エラーハンドリング強化
3. 使用例とドキュメント

この設計により、Python format構文のみに焦点を当てつつ、将来的な拡張性を確保した実装が可能になります。既存の優秀なフォーマット処理基盤を活用することで、開発効率と品質の両方を確保できます。