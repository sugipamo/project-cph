"""
カスタム禁止ワード・パターンの定義
ruffと組み合わせて使用する追加チェック
"""

# 禁止ワード（コメント・文字列・変数名で使用禁止）
FORBIDDEN_WORDS = [
    "todo",          # TODOコメントの禁止
    "fixme",         # FIXMEコメントの禁止
    "hack",          # HACKコメントの禁止
    "temp",          # 一時的な変数名の禁止
    "tmp",           # 一時的な変数名の禁止
    "foo",           # プレースホルダー変数名の禁止
    "bar",           # プレースホルダー変数名の禁止
    "baz",           # プレースホルダー変数名の禁止
    "dummy",         # ダミー変数名の禁止
    "test123",       # テスト用変数名の禁止
    "debug",         # デバッグ用コードの禁止（ロガー以外）
]

# 禁止パターン（正規表現）
FORBIDDEN_PATTERNS = [
    r"print\s*\(",           # print文の使用禁止（ロガー推奨）
    r"import\s+pdb",         # pdbデバッガーの禁止
    r"breakpoint\s*\(",      # breakpoint()の禁止
    r"# noqa:",              # noqaコメントの制限
    r"type:\s*ignore",       # type: ignoreの制限
    r"\.strip\(\)\.strip\(\)", # 重複するstrip()
    r"len\(.+\)\s*==\s*0",   # len(x) == 0 instead of not x
    r"len\(.+\)\s*>\s*0",    # len(x) > 0 instead of x
]

# 関数・クラス名の命名規則違反
NAMING_VIOLATIONS = [
    r"^[A-Z][a-z]+[A-Z]",    # camelCaseの禁止（snake_case推奨）
    r"^[a-z]+[A-Z]",         # mixedCaseの禁止
    r"^_[A-Z]",              # _PascalCaseの禁止
    r".*[0-9]$",             # 末尾数字の制限
]

# 許可される最大行数
MAX_FUNCTION_LINES = 50
MAX_CLASS_LINES = 200
MAX_FILE_LINES = 500

# 許可される最大複雑度
MAX_CYCLOMATIC_COMPLEXITY = 10
MAX_COGNITIVE_COMPLEXITY = 15

# 必須docstring
REQUIRE_DOCSTRING = {
    "modules": True,
    "classes": True,
    "functions": True,
    "methods": True,
}
