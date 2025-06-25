"""
依存関係グラフ生成機能のテスト
"""

import sys
import shutil
from pathlib import Path

# プロトタイプのパスを追加
sys.path.insert(0, "src_check/src_processors/auto_correct/import_dependency_reorganizer")

from simple_import_analyzer import SimpleImportAnalyzer
from dependency_calculator import DependencyCalculator
from graph_visualizer import DependencyGraphVisualizer

def test_graph_generation():
    """グラフ生成機能のテスト"""
    
    print("📊 依存関係グラフ生成テスト")
    print("=" * 60)
    
    # テスト用プロジェクトを作成
    test_src = Path("test_src_graph")
    if test_src.exists():
        shutil.rmtree(test_src)
    test_src.mkdir()
    
    # サンプルプロジェクト構造を作成
    create_sample_project(test_src)
    
    print("✅ テストプロジェクト作成完了")
    
    # 依存関係解析
    print("\n1️⃣ 依存関係を解析中...")
    analyzer = SimpleImportAnalyzer(test_src)
    analyzer.analyze_all_files()
    
    print(f"  解析完了: {len(analyzer.file_imports)}ファイル")
    
    # 依存関係計算
    calculator = DependencyCalculator(analyzer)
    depth_map = calculator.calculate_dependency_depths()
    
    print(f"  深度計算完了: 最大深度 {max(depth_map.values()) if depth_map else 0}")
    
    # グラフ生成
    print("\n2️⃣ グラフを生成中...")
    visualizer = DependencyGraphVisualizer(analyzer, calculator)
    
    output_dir = Path("test_graphs")
    output_dir.mkdir(exist_ok=True)
    
    # 各種形式で出力
    print("  📝 DOT形式...")
    visualizer.generate_dot(output_dir / "test_graph.dot", depth_map)
    
    print("  📝 Mermaid形式...")
    visualizer.generate_mermaid(output_dir / "test_graph.md", depth_map)
    
    print("  📝 JSON形式...")
    visualizer.generate_json_graph(output_dir / "test_graph.json", depth_map)
    
    print("  📝 ASCIIツリー...")
    visualizer.generate_ascii_tree(output_dir / "test_tree.txt")
    
    print("  📝 要約レポート...")
    visualizer.generate_summary_report(output_dir / "test_report.md")
    
    # HTMLビューアを生成
    print("  🌐 HTMLビューア生成...")
    from main_v2 import _generate_html_viewer
    _generate_html_viewer(
        output_dir / "test_graph.json",
        output_dir / "test_viewer.html"
    )
    
    print(f"\n✅ グラフ生成完了！")
    print(f"📁 出力先: {output_dir.absolute()}")
    
    # 生成されたファイルを表示
    print("\n生成されたファイル:")
    for file in sorted(output_dir.glob("*")):
        size = file.stat().st_size
        print(f"  - {file.name} ({size:,} bytes)")
    
    # サンプル出力を表示
    print("\n3️⃣ サンプル出力")
    
    # ASCIIツリーの最初の部分を表示
    print("\n[ASCIIツリー]")
    tree_content = (output_dir / "test_tree.txt").read_text()
    print('\n'.join(tree_content.split('\n')[:20]))
    print("...")
    
    # Mermaidグラフの最初の部分を表示
    print("\n[Mermaidグラフ]")
    mermaid_content = (output_dir / "test_graph.md").read_text()
    print('\n'.join(mermaid_content.split('\n')[:15]))
    print("...")
    
    print("\n" + "=" * 60)
    print("✨ テスト完了！")
    print("HTMLビューアを開くには: open test_graphs/test_viewer.html")
    print("=" * 60)

def create_sample_project(root: Path):
    """テスト用のサンプルプロジェクトを作成"""
    
    # 基底モジュール（深度0）
    (root / "__init__.py").write_text("")
    
    (root / "constants.py").write_text("""
# 定数定義
API_VERSION = "1.0.0"
DEBUG = True
""")
    
    (root / "types.py").write_text("""
# 型定義
from typing import Dict, List, Optional

UserDict = Dict[str, str]
ConfigDict = Dict[str, any]
""")
    
    # ユーティリティ層（深度1）
    (root / "validators.py").write_text("""
# バリデーター
from .types import UserDict

def validate_user(user: UserDict) -> bool:
    return "name" in user and "email" in user
""")
    
    (root / "formatters.py").write_text("""
# フォーマッター
from .constants import API_VERSION

def format_version(prefix: str = "") -> str:
    return f"{prefix}v{API_VERSION}"
""")
    
    # サービス層（深度2）
    (root / "user_service.py").write_text("""
# ユーザーサービス
from .types import UserDict
from .validators import validate_user

class UserService:
    def create_user(self, data: UserDict) -> UserDict:
        if validate_user(data):
            return data
        raise ValueError("Invalid user data")
""")
    
    (root / "config_service.py").write_text("""
# 設定サービス
from .types import ConfigDict
from .constants import DEBUG
from .formatters import format_version

class ConfigService:
    def get_config(self) -> ConfigDict:
        return {
            "debug": DEBUG,
            "version": format_version("API ")
        }
""")
    
    # ハンドラー層（深度3）
    (root / "api_handler.py").write_text("""
# APIハンドラー
from .user_service import UserService
from .config_service import ConfigService
from .types import UserDict, ConfigDict

class APIHandler:
    def __init__(self):
        self.user_service = UserService()
        self.config_service = ConfigService()
    
    def handle_request(self, user_data: UserDict) -> dict:
        user = self.user_service.create_user(user_data)
        config = self.config_service.get_config()
        return {"user": user, "config": config}
""")
    
    # アプリケーション層（深度4）
    (root / "main.py").write_text("""
# メインアプリケーション
from .api_handler import APIHandler

def main():
    handler = APIHandler()
    result = handler.handle_request({
        "name": "Test User",
        "email": "test@example.com"
    })
    print(result)

if __name__ == "__main__":
    main()
""")
    
    # 循環依存のテスト
    (root / "circular_a.py").write_text("""
# 循環依存A
from .circular_b import function_b

def function_a():
    return function_b() + "_a"
""")
    
    (root / "circular_b.py").write_text("""
# 循環依存B
from .circular_a import function_a

def function_b():
    return "b"

def function_b2():
    try:
        return function_a()
    except:
        return "b2"
""")

if __name__ == "__main__":
    test_graph_generation()