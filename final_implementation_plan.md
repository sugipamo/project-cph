# 将来拡張に強いテスト結果フォーマッタ - 最終実装プラン

## 🎯 概要

`./cph.sh test`コマンドを拡張して、env.jsonで好きなフォーマットで結果を見られるようにする実装プランです。将来の変更に強い設計を重視し、段階的な実装を行います。

## 📊 実装コスト総合見積もり

| 実装レベル | 時間 | ファイル数 | リスク | 拡張性 | 推奨度 |
|------------|------|------------|--------|--------|--------|
| **推奨: 将来拡張対応版** | **17-22h** | **13** | **中** | **最高** | **⭐⭐⭐⭐⭐** |
| 低コスト版 | 3-4h | 2 | 低 | 低 | ⭐⭐⭐ |
| 中コスト版 | 6-8h | 5 | 中 | 中 | ⭐⭐⭐⭐ |

## 🏗️ アーキテクチャ設計（将来拡張対応版）

### 設計原則
1. **Strategy Pattern**: プラグイン可能なフォーマッタ
2. **Factory Pattern**: 設定に基づく動的生成
3. **Adapter Pattern**: 既存コードとの互換性
4. **Template Method**: 共通処理の抽象化
5. **Dependency Injection**: テスタブルな設計

### コア抽象化
```python
# 基本データ構造（不変）
@dataclass(frozen=True)
class TestResult:
    test_name: str
    status: TestStatus  # PASS/FAIL/ERROR/SKIP
    expected_output: Optional[str] = None
    actual_output: Optional[str] = None
    error_message: Optional[str] = None
    execution_time: Optional[float] = None

# フォーマッタ抽象基底クラス
class TestResultFormatter(ABC):
    @abstractmethod
    def format_single_result(self, result: TestResult, options: FormatOptions) -> str
    
    @abstractmethod
    def format_summary(self, results: List[TestResult], options: FormatOptions) -> str
```

## 🚀 段階的実装プラン

### Phase 1: 基盤構築 (6-8h)

#### 1.1 コア抽象化の実装 (2h)
**作成ファイル:**
- `src/operations/formatters/base_formatter.py`
- `src/operations/formatters/__init__.py`

**実装内容:**
- `TestResult`, `FormatOptions`, `TestStatus` データクラス
- `TestResultFormatter` 抽象基底クラス
- 基本的な型定義とインターフェース

#### 1.2 基本フォーマッタの実装 (3-4h)
**作成ファイル:**
- `src/operations/formatters/detailed_formatter.py` (現在のデフォルト再現)
- `src/operations/formatters/compact_formatter.py`
- `src/operations/formatters/json_formatter.py`

**実装内容:**
```python
# DetailedFormatter: 現在の出力形式を完全再現
class DetailedFormatter(TestResultFormatter):
    def format_single_result(self, result: TestResult, options: FormatOptions) -> str:
        # 既存の "Testing sample-1.in\n✓ PASS" 形式
        pass
    
    def format_summary(self, results: List[TestResult], options: FormatOptions) -> str:
        # "Tests: X passed, Y failed, Z errors, N total"
        pass
```

#### 1.3 ファクトリーとレジストリ (2h)
**作成ファイル:**
- `src/operations/formatters/formatter_factory.py`

**実装内容:**
- `FormatterRegistry`: プラグイン可能なフォーマッタ管理
- `FormatterFactory`: 設定に基づくフォーマッタ生成
- デフォルトフォーマッタの自動登録

### Phase 2: 統合とテスト (6-8h)

#### 2.1 既存コードとの統合 (3-4h)
**修正ファイル:**
- `src/operations/factory/unified_request_factory.py`

**実装内容:**
```python
class ComplexRequestStrategy(RequestCreationStrategy):
    def create_request(self, step: Step, context: Any, env_manager: EnvironmentManager):
        if step.type == StepType.TEST:
            # 新旧システムの共存
            if self._has_format_options(step):
                # 新システム使用
                return self._create_formatted_test_request(step, context, env_manager)
            else:
                # 既存システム使用（完全互換性保持）
                return self._create_legacy_test_request(step, context, env_manager)
```

#### 2.2 設定統合 (1h)
**作成ファイル:**
- `src/operations/formatters/config_integration.py`

**実装内容:**
- env.jsonからフォーマット設定を解決
- デフォルト値の適用
- 設定妥当性の検証

#### 2.3 包括的テスト (2-3h)
**作成ファイル:**
- `tests/formatters/test_base_formatter.py`
- `tests/formatters/test_detailed_formatter.py`
- `tests/formatters/test_compact_formatter.py`
- `tests/formatters/test_json_formatter.py`
- `tests/formatters/test_formatter_factory.py`
- `tests/formatters/test_integration.py`

### Phase 3: 安全な公開とフィードバック (3-4h)

#### 3.1 後方互換性保証 (1-2h)
**作成ファイル:**
- `src/operations/formatters/compatibility_adapter.py`

**実装内容:**
- レガシーアダプター
- 自動フォールバック機能
- エラー監視と安全策

#### 3.2 プラグインシステム (1h)
**実装内容:**
- 外部フォーマッタの登録機能
- プラグイン検出システム
- 動的読み込み機能

#### 3.3 ドキュメントとサンプル (1h)
**作成ファイル:**
- `docs/formatter_usage.md`
- サンプルenv.json設定

### Phase 4: 高度な機能と最適化 (2-3h)

#### 4.1 カスタムテンプレート機能 (1-2h)
**実装内容:**
- Jinja2風のテンプレートエンジン
- ユーザー定義テンプレート
- テンプレート妥当性検証

#### 4.2 パフォーマンス最適化 (1h)
**実装内容:**
- フォーマッタキャッシュ
- 並列処理対応
- メモリ効率の改善

## 📁 ファイル構成

```
src/operations/formatters/
├── __init__.py
├── base_formatter.py           # 抽象基底クラス
├── detailed_formatter.py       # デフォルト（現在の形式）
├── compact_formatter.py        # コンパクト形式
├── json_formatter.py          # JSON形式
├── formatter_factory.py       # ファクトリーとレジストリ
├── config_integration.py      # env.json統合
├── compatibility_adapter.py   # 後方互換性
└── template_engine.py         # カスタムテンプレート

tests/formatters/
├── __init__.py
├── conftest.py                # テスト共通設定
├── test_base_formatter.py
├── test_detailed_formatter.py
├── test_compact_formatter.py
├── test_json_formatter.py
├── test_formatter_factory.py
├── test_config_integration.py
├── test_compatibility.py
└── test_integration.py       # E2Eテスト
```

## 🔧 env.json設定例

### 基本設定
```json
{
  "python": {
    "commands": {
      "test": {
        "steps": [
          {
            "type": "test",
            "cmd": ["python3", "{workspace_path}/{source_file_name}"],
            "output_format": "detailed"
          }
        ]
      }
    }
  }
}
```

### 高度な設定
```json
{
  "python": {
    "commands": {
      "test": {
        "steps": [
          {
            "type": "test",
            "cmd": ["python3", "{workspace_path}/{source_file_name}"],
            "output_format": "detailed",
            "format_options": {
              "show_colors": true,
              "show_timing": true,
              "show_diff": true,
              "max_output_lines": 20,
              "custom_templates": {
                "pass": "✅ {test_name} - PASSED ({execution_time:.2f}s)",
                "fail": "❌ {test_name} - FAILED",
                "error": "💥 {test_name} - ERROR: {error_message}"
              }
            }
          }
        ]
      },
      "test_compact": {
        "aliases": ["tc"],
        "steps": [
          {
            "type": "test",
            "cmd": ["python3", "{workspace_path}/{source_file_name}"],
            "output_format": "compact"
          }
        ]
      },
      "test_json": {
        "aliases": ["tj"],
        "steps": [
          {
            "type": "test",
            "cmd": ["python3", "{workspace_path}/{source_file_name}"],
            "output_format": "json",
            "format_options": {
              "include_timing": true,
              "pretty_print": true
            }
          }
        ]
      }
    }
  }
}
```

## 📊 出力例

### Detailed Format (デフォルト)
```
Testing sample-1.in
✓ PASS (0.023s)
Testing sample-2.in
✗ FAIL
Expected:
2
Got:
1
Testing sample-3.in
✗ ERROR
Program failed with error:
ValueError: invalid literal for int()

Tests: 1 passed, 1 failed, 1 error, 3 total
```

### Compact Format
```
[✓] sample-1.in [✗] sample-2.in [E] sample-3.in
pass: 1 | fail: 1 | error: 1
```

### JSON Format
```json
{
  "summary": {
    "total_tests": 3,
    "passed": 1,
    "failed": 1,
    "errors": 1
  },
  "results": [
    {
      "test_name": "sample-1.in",
      "status": "pass",
      "execution_time": 0.023
    },
    {
      "test_name": "sample-2.in",
      "status": "fail",
      "expected_output": "2",
      "actual_output": "1"
    },
    {
      "test_name": "sample-3.in",
      "status": "error",
      "error_message": "ValueError: invalid literal for int()"
    }
  ]
}
```

## 🎯 プラグイン拡張例

### カスタムMarkdownフォーマッタ
```python
# plugins/markdown_formatter.py
class MarkdownFormatter(TestResultFormatter):
    def format_single_result(self, result: TestResult, options: FormatOptions) -> str:
        if result.status == TestStatus.PASS:
            return f"- ✅ **{result.test_name}**: PASSED"
        elif result.status == TestStatus.FAIL:
            return f"- ❌ **{result.test_name}**: FAILED\n  - Expected: `{result.expected_output}`\n  - Got: `{result.actual_output}`"
        else:
            return f"- 💥 **{result.test_name}**: ERROR - {result.error_message}"

# 使用例
factory.register_plugin_formatter(MarkdownFormatter())
```

### Slack通知フォーマッタ
```python
class SlackFormatter(TestResultFormatter):
    def format_summary(self, results: List[TestResult], options: FormatOptions) -> str:
        total = len(results)
        passed = sum(1 for r in results if r.status == TestStatus.PASS)
        
        if passed == total:
            return f":white_check_mark: All {total} tests passed!"
        else:
            failed = total - passed
            return f":x: {failed}/{total} tests failed"
```

## 🚀 使用方法

### 1. 基本的な使用
```bash
# デフォルト（詳細形式）
./cph.sh python local test abc300 a

# コンパクト形式
./cph.sh python local test_compact abc300 a

# JSON形式
./cph.sh python local test_json abc300 a
```

### 2. env.json設定での制御
ユーザーは自分のenv.jsonファイルを編集するだけで、テスト結果の表示形式を完全にカスタマイズできます。

### 3. プラグインフォーマッタの追加
```python
# custom_formatters.py を作成
from src.operations.formatters.formatter_factory import FormatterFactory

factory = FormatterFactory()
factory.register_plugin_formatter(MyCustomFormatter())
```

## ✅ 成功基準

1. **機能性**: 3種類以上のフォーマット（detailed, compact, json）
2. **拡張性**: 新しいフォーマッタを10行以下で追加可能
3. **互換性**: 既存のテストが100%パス
4. **性能**: 実行時間の増加が5%以内
5. **使いやすさ**: env.jsonの設定だけでカスタマイズ完了

## 🎯 将来の拡張可能性

この設計により、以下の機能を容易に追加できます：

1. **リアルタイム表示**: ストリーミング形式での結果表示
2. **統計情報**: 実行時間分析、傾向分析
3. **外部連携**: CI/CD、Slack、Discord通知
4. **視覚化**: グラフ、チャート生成
5. **フィルタリング**: 特定の条件での結果絞り込み
6. **テンプレートエンジン**: 高度なカスタマイズ

## 📈 投資対効果

- **短期効果**: すぐに使える3つのフォーマット
- **中期効果**: ユーザーのカスタマイズによる生産性向上
- **長期効果**: プラグインエコシステムの構築

この実装により、将来どのような要件変更があっても、既存機能を破損させることなく柔軟に対応できるシステムが構築されます。

<function_calls>
<invoke name="TodoWrite">
<parameter name="todos">[{"id": "1", "content": "\u5c06\u6765\u62e1\u5f35\u306b\u5f37\u3044\u8a2d\u8a08\u30d1\u30bf\u30fc\u30f3\u3092\u8abf\u67fb", "status": "completed", "priority": "high"}, {"id": "2", "content": "\u30d7\u30e9\u30b0\u30a4\u30f3\u53ef\u80fd\u306a\u30d5\u30a9\u30fc\u30de\u30c3\u30bf\u30a2\u30fc\u30ad\u30c6\u30af\u30c1\u30e3\u3092\u8a2d\u8a08", "status": "completed", "priority": "high"}, {"id": "3", "content": "\u65e2\u5b58\u30b3\u30fc\u30c9\u3068\u306e\u4e92\u63db\u6027\u3092\u4fdd\u3064\u30a4\u30f3\u30bf\u30fc\u30d5\u30a7\u30fc\u30b9\u8a2d\u8a08", "status": "completed", "priority": "medium"}, {"id": "4", "content": "\u30c6\u30b9\u30c8\u30d5\u30ec\u30fc\u30e0\u30ef\u30fc\u30af\u3068\u306e\u7d71\u5408\u3092\u691c\u8a0e", "status": "completed", "priority": "medium"}, {"id": "5", "content": "\u6bb5\u968e\u7684\u79fb\u884c\u30d7\u30e9\u30f3\u3092\u4f5c\u6210", "status": "completed", "priority": "high"}]