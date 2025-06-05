# フォーマット関数統合計画

## 1. 現状分析

### 1.1 機能重複度分析
- **低重複**: format_utils.py の基本機能（独立性高い）
- **中重複**: execution_context_formatter_pure.py （format_utilsに依存）
- **低重複**: output_manager_formatter_pure.py （独立性高い）

### 1.2 使用箇所分析
- `format_with_missing_keys`: 8ファイルで使用（最も多い）
- `format_with_context`: 主にテストで使用
- `create_format_dict`: ExecutionContextで使用
- `extract_output_data`系: OutputManagerで専用使用

## 2. 統合アーキテクチャ設計

### 2.1 階層構造
```
src/pure_functions/formatting/
├── core/                           # 基底レイヤー
│   ├── string_formatter.py        # 基本文字列フォーマット
│   ├── template_processor.py      # テンプレート処理
│   └── validation.py              # 共通バリデーション
├── specialized/                    # 特化レイヤー
│   ├── execution_formatter.py     # ExecutionContext特化
│   ├── output_formatter.py        # 出力フォーマット特化
│   └── path_formatter.py          # パス関連特化
└── __init__.py                     # 統合API公開
```

### 2.2 基底レイヤー設計

#### string_formatter.py
```python
@lru_cache(maxsize=512)
def extract_format_keys(template: str) -> List[str]

def format_with_missing_keys(template: str, **kwargs) -> Tuple[str, List[str]]

def format_with_context(template: str, context: Dict[str, Any]) -> str

class SafeFormatter:
    """セーフなフォーマット処理クラス"""
```

#### template_processor.py
```python
def build_path_template(base: str, *parts: str) -> str

def validate_template_keys(template: str, required_keys: List[str]) -> Tuple[bool, List[str]]

class TemplateValidator:
    """テンプレートバリデーションクラス"""
```

#### validation.py
```python
def validate_format_data(data: Any, required_fields: List[str]) -> Tuple[bool, Optional[str]]

class FormatDataValidator:
    """フォーマットデータバリデーションクラス"""
```

### 2.3 特化レイヤー設計

#### execution_formatter.py
```python
@dataclass(frozen=True)
class ExecutionFormatData:
    """ExecutionContext用フォーマットデータ"""

def create_execution_format_dict(data: ExecutionFormatData) -> Dict[str, str]

def format_execution_template(template: str, data: ExecutionFormatData) -> Tuple[str, set]

def get_docker_naming_context(data: ExecutionFormatData, **kwargs) -> dict
```

#### output_formatter.py
```python
@dataclass(frozen=True)
class OutputFormatData:
    """出力フォーマット用データ"""

def extract_output_data(result) -> OutputFormatData

def format_output_content(data: OutputFormatData) -> str

def decide_output_action(show_output: bool, data: OutputFormatData) -> Tuple[bool, str]
```

## 3. 段階的移行計画

### Phase 1: 基底レイヤー作成
1. `src/pure_functions/formatting/core/` ディレクトリ作成
2. 既存の format_utils.py から基本機能を抽出・移植
3. パフォーマンス最適化とキャッシング機能保持
4. 既存APIとの完全互換性確保

### Phase 2: 特化レイヤー作成
1. `src/pure_functions/formatting/specialized/` ディレクトリ作成
2. execution_context_formatter_pure.py を execution_formatter.py に移植
3. output_manager_formatter_pure.py を output_formatter.py に移植
4. 基底レイヤーへの依存関係を整理

### Phase 3: 統合API作成
1. `src/pure_functions/formatting/__init__.py` で統合API公開
2. 既存の全インポートパスに対する互換性エイリアス提供
3. 新しい統合APIの追加（推奨パス）

### Phase 4: 段階的移行
1. 新規コードから新しいAPIを使用
2. 既存コードの段階的移行（テスト駆動）
3. 旧APIの非推奨化（警告付き）

### Phase 5: クリーンアップ
1. 旧ファイルの削除
2. テストの統合と整理
3. ドキュメント更新

## 4. 互換性維持戦略

### 4.1 エイリアス提供
```python
# src/pure_functions/formatting/__init__.py
from .core.string_formatter import format_with_missing_keys
from .specialized.execution_formatter import (
    ExecutionFormatData as ExecutionFormatData_New,
    create_execution_format_dict
)

# 互換性エイリアス
from .specialized.execution_formatter import create_execution_format_dict as create_format_dict
```

### 4.2 段階的警告
```python
import warnings

def deprecated_function(*args, **kwargs):
    warnings.warn("This function is deprecated. Use new_function instead.", 
                 DeprecationWarning, stacklevel=2)
    return new_function(*args, **kwargs)
```

## 5. パフォーマンス最適化

### 5.1 キャッシング戦略
- LRUキャッシュの統一管理
- テンプレートキー抽出の最適化
- 正規表現パターンの共有

### 5.2 メモリ効率
- dataclassの frozen=True 活用
- 文字列処理の最適化
- 不要なオブジェクト生成の削減

## 6. テスト戦略

### 6.1 既存テストの保持
- 全ての既存テストが通ることを保証
- 性能テストの追加
- 互換性テストの追加

### 6.2 新規テストの追加
- 統合APIのテスト
- パフォーマンステスト
- エラーハンドリングテスト

## 7. 成功指標

1. **機能性**: 全ての既存機能が正常動作
2. **性能**: 現在と同等以上のパフォーマンス
3. **保守性**: コードの重複削減（目標: 30%削減）
4. **使いやすさ**: 新しいAPIの使用促進

## 8. リスク管理

### 8.1 リスク要素
- 既存コードの破綻
- パフォーマンス劣化
- 移行作業の複雑化

### 8.2 対策
- 段階的移行による影響最小化
- 包括的テストによる品質保証
- ロールバック計画の準備

## 9. 実装優先順位

1. **高優先**: 基底レイヤー（string_formatter.py）
2. **中優先**: 特化レイヤー（execution_formatter.py）
3. **低優先**: 統合API（__init__.py）
4. **保守**: クリーンアップとドキュメント