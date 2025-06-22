#!/usr/bin/env python3
"""
dict.get()自動変換ツール
dict.get()をKeyErrorハンドリングまたは明示的なチェックに変換する
"""

import argparse
import ast
import re
import sys
from pathlib import Path
from typing import List, Tuple


class DictGetConverter(ast.NodeTransformer):
    """dict.get()呼び出しを適切な形式に変換するAST変換器"""

    def __init__(self):
        self.conversions = []

    def visit_Call(self, node):
        # 子ノードを先に処理
        self.generic_visit(node)

        # .get()メソッド呼び出しをチェック
        if (isinstance(node.func, ast.Attribute) and
            node.func.attr == 'get' and
            len(node.args) >= 1):

            # dict.get(key) -> dict[key] (KeyErrorを発生させる)
            if len(node.args) == 1:
                self.conversions.append(f"行 {node.lineno}: dict.get(key) -> dict[key]")
                return ast.Subscript(
                    value=node.func.value,
                    slice=node.args[0],
                    ctx=ast.Load()
                )

            # dict.get(key, default) -> dict[key] (強制変換、デフォルト値無視)
            # プロジェクト方針：デフォルト値禁止、KeyErrorで問題を表面化
            if len(node.args) == 2:
                self.conversions.append(f"行 {node.lineno}: dict.get(key, default) -> dict[key]")
                return ast.Subscript(
                    value=node.func.value,
                    slice=node.args[0],
                    ctx=ast.Load()
                )

        return node

    def _is_falsy_default(self, node):
        """デフォルト値がFalsyかどうかを判定"""
        if isinstance(node, ast.Constant):
            return node.value in (None, False, 0, "", [])
        if isinstance(node, ast.NameConstant):  # Python 3.7以前の互換性
            return node.value in (None, False)
        return bool((isinstance(node, ast.List) and len(node.elts) == 0) or (isinstance(node, ast.Dict) and len(node.keys) == 0))


class RegexBasedConverter:
    """正規表現ベースのシンプル変換器（フォールバック用）"""

    def __init__(self):
        self.patterns = [
            # dict.get(key) -> dict[key]
            (r'(\w+)\.get\(([^,)]+)\)', r'\1[\2]'),
            # dict.get(key, 任意のデフォルト値) -> dict[key] (強制変換)
            (r'(\w+)\.get\(([^,)]+),\s*[^)]+\)', r'\1[\2]'),
        ]

    def convert_line(self, line: str) -> Tuple[str, bool]:
        """行内のdict.get()を変換"""
        converted = False

        for pattern, replacement in self.patterns:
            new_line = re.sub(pattern, replacement, line)
            if new_line != line:
                line = new_line
                converted = True

        return line, converted


def convert_file_ast(file_path: Path, dry_run: bool = True) -> List[str]:
    """ASTベースでファイルを変換"""
    try:
        with open(file_path, encoding='utf-8') as f:
            content = f.read()

        tree = ast.parse(content, filename=str(file_path))
        converter = DictGetConverter()
        new_tree = converter.visit(tree)

        if converter.conversions:
            if not dry_run:
                # 変換されたASTをコードに戻す
                import astor  # 必要に応じてインストール
                new_content = astor.to_source(new_tree)

                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)

            return converter.conversions

        return []

    except ImportError as e:
        raise ImportError(f"Required dependency 'astor' not available: {e}") from e
    except (SyntaxError, UnicodeDecodeError) as e:
        raise Exception(f"Failed to parse file {file_path}: {e}") from e


def convert_file_regex(file_path: Path, dry_run: bool = True) -> List[str]:
    """正規表現ベースでファイルを変換"""
    try:
        with open(file_path, encoding='utf-8') as f:
            lines = f.readlines()

        converter = RegexBasedConverter()
        conversions = []
        converted_lines = []
        file_changed = False

        for line_num, line in enumerate(lines, 1):
            # コメント行はスキップ
            if line.strip().startswith('#'):
                converted_lines.append(line)
                continue

            new_line, changed = converter.convert_line(line)
            converted_lines.append(new_line)

            if changed:
                file_changed = True
                conversions.append(f"行 {line_num}: {line.strip()} -> {new_line.strip()}")

        if file_changed and not dry_run:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(converted_lines)

        return conversions

    except (UnicodeDecodeError, OSError) as e:
        return [f"ファイル読み込みエラー: {e}"]


def find_dict_get_files(src_dir: Path) -> List[Path]:
    """dict.get()を使用しているファイルを検索"""
    import glob

    files_with_get = []
    get_pattern = re.compile(r'\.get\(')
    comment_pattern = re.compile(r'#.*$')

    for file_path in glob.glob(str(src_dir / '**/*.py'), recursive=True):
        try:
            with open(file_path, encoding='utf-8') as f:
                content = f.read()

            # コメントを除去してチェック
            lines = content.split('\n')
            has_get = False

            for line in lines:
                clean_line = comment_pattern.sub('', line)
                if get_pattern.search(clean_line):
                    has_get = True
                    break

            if has_get:
                files_with_get.append(Path(file_path))

        except (UnicodeDecodeError, OSError):
            continue

    return files_with_get


def main():
    parser = argparse.ArgumentParser(description="dict.get()自動変換ツール")
    parser.add_argument("path", nargs="?", default="src/",
                       help="変換対象のディレクトリまたはファイル (デフォルト: src/)")
    parser.add_argument("--dry-run", action="store_true",
                       help="変換内容をプレビューのみ（実際には変更しない）")
    parser.add_argument("--regex-only", action="store_true",
                       help="正規表現ベースの変換のみ使用（ASTを使わない）")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="詳細出力")

    args = parser.parse_args()

    target_path = Path(args.path)

    if not target_path.exists():
        print(f"エラー: パス '{target_path}' が見つかりません")
        sys.exit(1)

    # 対象ファイルを収集
    if target_path.is_file():
        target_files = [target_path] if target_path.suffix == '.py' else []
    else:
        target_files = find_dict_get_files(target_path)

    if not target_files:
        print("✅ dict.get()を使用しているファイルが見つかりませんでした")
        return

    print(f"📁 {len(target_files)}個のファイルでdict.get()を検出しました")

    if args.dry_run:
        print("🔍 プレビューモード（実際の変更は行いません）")

    total_conversions = 0

    for file_path in target_files:
        relative_path = file_path.relative_to(Path.cwd()) if file_path.is_absolute() else file_path

        if args.verbose:
            print(f"\n📄 処理中: {relative_path}")

        # 変換実行
        if args.regex_only:
            conversions = convert_file_regex(file_path, args.dry_run)
        else:
            conversions = convert_file_ast(file_path, args.dry_run)

        if conversions:
            print(f"🔧 {relative_path}:")
            for conversion in conversions:
                print(f"   {conversion}")
            total_conversions += len(conversions)
        elif args.verbose:
            print("   変更なし")

    print("\n📊 変換サマリー:")
    print(f"   対象ファイル: {len(target_files)}個")
    print(f"   変換箇所: {total_conversions}箇所")

    if args.dry_run and total_conversions > 0:
        print("\n💡 実際に変換するには --dry-run を外して再実行してください")
    elif total_conversions > 0:
        print("✅ 変換が完了しました")
        print("⚠️  変換後は必ずテストを実行して動作確認してください")


if __name__ == "__main__":
    main()
