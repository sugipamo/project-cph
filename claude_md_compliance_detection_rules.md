# CLAUDE.md準拠性検知ルール

## 概要

このドキュメントは、`scripts/test.py`で検知すべきCLAUDE.mdルール違反パターンの詳細な条件を定義します。

## 1. デフォルト値使用禁止ルール

### 1.1 関数/メソッド引数でのデフォルト値使用

**検知対象パターン:**
```python
def func(arg="default"):          # 文字列デフォルト値
def func(arg=0):                  # 数値デフォルト値
def func(arg=0.0):                # 浮動小数点デフォルト値
def func(arg=None):               # Noneデフォルト値
def func(arg=True):               # ブールデフォルト値
def func(arg=[]):                 # リストデフォルト値
def func(arg={}):                 # 辞書デフォルト値
def func(arg=set()):              # セットデフォルト値
def func(arg=lambda: None):       # 関数デフォルト値
```

**正規表現パターン:**
```regex
def\s+\w+\([^)]*\w+\s*=[^,)]+
```

**除外条件:**
- テストファイル内（`tests/`配下）
- `typing.Optional[T] = None`形式の型ヒント（型チェック用途）

### 1.2 dict.get()メソッドでのデフォルト値使用

**検知対象パターン:**
```python
dict.get(key, default)
mapping.get('key', 'default')
config.get('setting', None)
```

**正規表現パターン:**
```regex
\w+\.get\([^,)]+,\s*[^)]+\)
```

**除外条件:**
- テストファイル内
- `dict.get(key)`（デフォルト値なし）は許可

### 1.3 getattr()でのデフォルト値使用

**検知対象パターン:**
```python
getattr(obj, 'attr', default)
getattr(instance, attribute, None)
getattr(self, name, "default")
```

**正規表現パターン:**
```regex
getattr\([^,]+,\s*[^,]+,\s*[^)]+\)
```

### 1.4 'or' 演算子によるフォールバック

**検知対象パターン:**
```python
value = x or default
command_type = context_data["command"] or "help"
config = user_config or system_config
```

**正規表現パターン:**
```regex
\w+\s*=\s*[^|]+\s+or\s+[^|]+
```

**除外条件:**
- ブール値の論理演算（`if a or b:`）
- 関数呼び出し内の論理演算

## 2. 副作用配置ルール

### 2.1 infrastructure外でのファイルI/O操作

**検知対象パターン:**
```python
open(filename)
with open(path) as f:
pathlib.Path.open()
file.read()
file.write()
json.load()
json.dump()
```

**検知対象ディレクトリ:**
- `src/`配下（`src/infrastructure/`を除く）

**除外条件:**
- `src/infrastructure/`配下
- `tests/`配下

### 2.2 infrastructure外でのprint文使用

**検知対象パターン:**
```python
print("message")
print(f"formatted {message}")
print(variable)
```

**検知対象ディレクトリ:**
- `src/`配下（`src/infrastructure/`を除く）

**除外条件:**
- `src/infrastructure/`配下
- `tests/`配下
- デバッグ用print（`# DEBUG:`コメント付き）

### 2.3 外部システム呼び出し

**検知対象パターン:**
```python
subprocess.run()
subprocess.call()
os.system()
```

**検知対象ディレクトリ:**
- `src/`配下（`src/infrastructure/`を除く）

## 3. 設定管理ルール

### 3.1 存在しない設定の直接参照

**検知対象パターン:**
```python
config['nonexistent_key']
settings.get('undefined_setting')
```

**検知条件:**
設定キーが`config/system/*.json`に定義されていない場合

## 4. 検知実装のガイドライン

### 4.1 チェッカー実装の要件

1. **ファイルパス条件チェック**
   ```python
   def should_check_file(file_path: str) -> bool:
       # infrastructure配下は除外
       if '/infrastructure/' in file_path:
           return False
       # テストファイルは除外
       if '/tests/' in file_path:
           return False
       return file_path.endswith('.py')
   ```

2. **行番号とコンテキスト情報**
   ```python
   def report_violation(file_path: str, line_num: int, line_content: str, violation_type: str):
       return {
           'file': file_path,
           'line': line_num,
           'content': line_content.strip(),
           'violation': violation_type,
           'severity': 'error'
       }
   ```

### 4.2 優先度付け

1. **High Priority (即修正必要):**
   - 関数引数のデフォルト値使用
   - infrastructure外でのファイルI/O
   - dict.get()でのデフォルト値使用

2. **Medium Priority:**
   - getattr()でのデフォルト値使用
   - infrastructure外でのprint使用

3. **Low Priority:**
   - 'or' 演算子によるフォールバック（ケースバイケース）

## 5. 実装例

### 5.1 関数引数デフォルト値チェッカー

```python
import re
from typing import List, Dict

class FunctionDefaultChecker:
    def __init__(self):
        self.pattern = re.compile(r'def\s+\w+\([^)]*(\w+\s*=[^,)]+)')
    
    def check_file(self, file_path: str) -> List[Dict]:
        violations = []
        if not self.should_check_file(file_path):
            return violations
            
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                if match := self.pattern.search(line):
                    violations.append({
                        'file': file_path,
                        'line': line_num,
                        'content': line.strip(),
                        'violation': 'function_default_argument',
                        'severity': 'error'
                    })
        return violations
```

## 6. 統合指針

既存の`scripts/test.py`に以下のチェッカーを追加実装：

1. `FunctionDefaultChecker` - 関数引数デフォルト値検知
2. `GetattrDefaultChecker` - getattr()デフォルト値検知  
3. `OrFallbackChecker` - 'or'演算子フォールバック検知
4. `FileIoChecker` - infrastructure外ファイルI/O検知
5. `SideEffectChecker` - 副作用配置検知

これらのチェッカーを`run_all_checks()`メソッドに統合し、包括的なCLAUDE.md準拠性チェックを実現する。