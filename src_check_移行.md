以下は、**AST を使って動的に `print()` を `logger.append()` に書き換えたうえでモジュールとして実行・利用する完全なサンプルコード**です。`sub.py` のような外部ファイルに `print()` が含まれていることを想定し、**`importlib` + `ast` + `exec()`** を用いてモジュールとして動的に読み込みます。

---

## 📁 ディレクトリ構成例

```
.
├── main.py         # ← 実行ファイル（ここにサンプルコード）
├── sub.py          # ← print() を含むモジュール
```

---

## ✅ sub.py（例：変換対象）

```python
# sub.py
def hello():
    print("hello from sub")

def greet(name):
    print("Hi", name)
```

---

## ✅ main.py（AST変換 + 実行サンプル）

```python
import ast
import importlib.util
import sys
from types import ModuleType
from pathlib import Path

# ロガー定義
class Logger:
    def __init__(self):
        self.values = []

    def append(self, *args, sep=' ', end='\n', **kwargs):
        msg = sep.join(str(a) for a in args) + end
        self.values.append(msg)

logger = Logger()

# AST変換器：print(...) → logger.append(...)
class PrintTransformer(ast.NodeTransformer):
    def visit_Call(self, node):
        if isinstance(node.func, ast.Name) and node.func.id == "print":
            return ast.Call(
                func=ast.Attribute(value=ast.Name(id="logger", ctx=ast.Load()), attr="append", ctx=ast.Load()),
                args=node.args,
                keywords=node.keywords,
            )
        return self.generic_visit(node)

# サブモジュールのAST変換 & 実行
def load_and_patch_module(filepath: str, module_name: str, logger_obj) -> ModuleType:
    source_path = Path(filepath)
    source_code = source_path.read_text(encoding="utf-8")

    # ASTパース → 書き換え → コンパイル
    tree = ast.parse(source_code, filename=filepath)
    tree = PrintTransformer().visit(tree)
    ast.fix_missing_locations(tree)
    compiled = compile(tree, filename=filepath, mode="exec")

    # 新しいモジュールオブジェクト作成
    mod = ModuleType(module_name)
    mod.__file__ = str(source_path)
    mod.logger = logger_obj  # loggerをスコープに追加

    # 実行
    exec(compiled, mod.__dict__)
    sys.modules[module_name] = mod  # 他からimportできるよう登録
    return mod

# モジュール読み込み & 利用
if __name__ == "__main__":
    sub = load_and_patch_module("sub.py", "sub", logger)

    sub.hello()
    sub.greet("Alice")

    print("==== Captured Logs ====")
    for line in logger.values:
        print(line, end="")  # 改行は logger.append() で含まれている
```

---

## ✅ 実行結果（main.py）

```
==== Captured Logs ====
hello from sub
Hi Alice
```

---

## ✅ 解説ポイント

| 処理                 | 技術的説明                                   |
| ------------------ | --------------------------------------- |
| `ast.parse`        | `sub.py` の構文木を取得                        |
| `PrintTransformer` | `print(...)` を `logger.append(...)` に変換 |
| `exec()`           | AST から生成したコードをモジュール空間で実行                |
| `sys.modules[...]` | 他の箇所から `import sub` で使えるように登録           |

---

## ✅ 補足：この方法の強み

* `sub.py` のソースを**一切変更しなくてよい**
* `print()` を `logger.append()` に柔軟に置換可能
* `logger` によって出力を集めて後処理やテストに活用できる

---

必要であれば、キーワード引数の正確な取り扱いや、エラー処理、複数ファイル対応などの強化バージョンも提供可能です。
