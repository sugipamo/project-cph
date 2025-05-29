import re

def extract_format_keys(s: str):
    """
    文字列sからstr.format用のキー（{key}のkey部分）をリストで抽出する
    例: '/path/{foo}/{bar}.py' -> ['foo', 'bar']
    """
    return re.findall(r'{(\w+)}', s)

def format_with_missing_keys(s: str, **kwargs):
    """
    sの{key}をkwargsで置換し、新しい文字列と足りなかったキーのリストを返す
    例: s = '/path/{foo}/{bar}.py', kwargs={'foo': 'A'}
    -> ('/path/A/{bar}.py', ['bar'])
    """
    keys = extract_format_keys(s)
    missing = [k for k in keys if k not in kwargs]
    # 足りないキーはそのまま残すため、SafeDictを使う
    class SafeDict(dict):
        def __missing__(self, key):
            return '{' + key + '}'
    formatted = s.format_map(SafeDict(kwargs))
    return formatted, missing

if __name__ == "__main__":
    s = '/home/cphelper/project-cph/{contest_template_path}/{language_name}/main.py'
    print(extract_format_keys(s))  # ['contest_template_path', 'language_name']
    print(format_with_missing_keys(s, contest_template_path='abc'))
    # ('/home/cphelper/project-cph/abc/{language_name}/main.py', ['language_name']) 