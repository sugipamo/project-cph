"""
Phase 2機能のテストスクリプト
インポート更新、ファイル移動、構文検証の統合テスト
"""

import sys
import shutil
from pathlib import Path

# プロトタイプのパスを追加
sys.path.insert(0, "src_check/src_processors/auto_correct/import_dependency_reorganizer")

from simple_import_analyzer import SimpleImportAnalyzer
from dependency_calculator import DependencyCalculator
from import_updater_v3 import ImportUpdaterV3
from file_mover import FileMover
from syntax_validator import SyntaxValidator

def test_phase2_features():
    """Phase 2機能の統合テスト"""
    
    # テスト用プロジェクトを再作成
    test_src = Path("test_src_phase2")
    if test_src.exists():
        shutil.rmtree(test_src)
    test_src.mkdir()
    
    print("📁 テスト用プロジェクトを作成...")
    
    # より複雑な依存関係を持つプロジェクトを作成
    # 基底層（深度0）
    (test_src / "__init__.py").write_text("")
    
    (test_src / "constants.py").write_text("""
# 定数定義（誰にも依存しない）
API_VERSION = "1.0"
MAX_RETRIES = 3
""")
    
    # 深度1
    (test_src / "logger.py").write_text("""
# ロガー（constantsに依存）
from .constants import API_VERSION

class Logger:
    def __init__(self):
        self.version = API_VERSION
    
    def log(self, message):
        print(f"[v{self.version}] {message}")
""")
    
    (test_src / "config.py").write_text("""
# 設定管理（constantsに依存）
from .constants import MAX_RETRIES

class Config:
    def __init__(self):
        self.retries = MAX_RETRIES
    
    def get_retry_count(self):
        return self.retries
""")
    
    # 深度2
    (test_src / "database.py").write_text("""
# データベース（logger, configに依存）
from .logger import Logger
from .config import Config

class Database:
    def __init__(self):
        self.logger = Logger()
        self.config = Config()
    
    def connect(self):
        self.logger.log("Connecting to database...")
        return f"Connected with {self.config.get_retry_count()} retries"
""")
    
    # 深度3
    (test_src / "api_handler.py").write_text("""
# APIハンドラー（databaseに依存）
from .database import Database

class APIHandler:
    def __init__(self):
        self.db = Database()
    
    def handle_request(self):
        result = self.db.connect()
        return f"API: {result}"
""")
    
    # 深度4
    (test_src / "main.py").write_text("""
# メインアプリケーション（api_handlerに依存）
from .api_handler import APIHandler

def main():
    handler = APIHandler()
    print(handler.handle_request())

if __name__ == "__main__":
    main()
""")
    
    print("✅ テストプロジェクト作成完了")
    print("\n" + "=" * 60)
    print("🔍 Phase 2機能テスト開始")
    print("=" * 60)
    
    # 1. 依存関係解析
    print("\n1️⃣ 依存関係を解析...")
    analyzer = SimpleImportAnalyzer(test_src)
    analyzer.analyze_all_files()
    
    calculator = DependencyCalculator(analyzer)
    depth_map = calculator.calculate_dependency_depths(max_depth=5)
    
    print("\n📊 解析結果:")
    for file_path, depth in sorted(depth_map.items(), key=lambda x: x[1]):
        print(f"  深度{depth}: {file_path.name}")
    
    # 2. 移動計画を作成
    print("\n2️⃣ 移動計画を作成...")
    move_plan = {}
    
    for file_path, depth in depth_map.items():
        if depth == 0:
            continue  # 深度0は移動しない
        
        # 深度に基づいて移動先を決定
        if depth == 1:
            folder = "core"
        elif depth == 2:
            folder = "services"
        elif depth == 3:
            folder = "handlers"
        else:
            folder = f"app/level_{depth-3}"
        
        new_path = test_src / folder / file_path.stem / file_path.name
        move_plan[file_path] = new_path
    
    print(f"移動予定: {len(move_plan)}ファイル")
    for old, new in move_plan.items():
        print(f"  {old.name} → {new.relative_to(test_src)}")
    
    # 3. インポート更新のテスト
    print("\n3️⃣ インポート更新をテスト...")
    updater = ImportUpdaterV3(test_src)
    updater.set_move_plan(move_plan)
    
    # ドライランで確認
    import_changes = updater.update_all_files(dry_run=True)
    print(f"更新が必要なファイル: {len(import_changes)}個")
    
    if import_changes:
        # 最初のファイルの変更内容を表示
        first_file = list(import_changes.keys())[0]
        print(f"\n例: {first_file.name}の更新内容:")
        print("---変更前---")
        print(first_file.read_text()[:200] + "...\n")
        print("---変更後---")
        print(import_changes[first_file][:200] + "...\n")
    
    # 4. ファイル移動のテスト
    print("\n4️⃣ ファイル移動をテスト...")
    mover = FileMover(test_src, use_git=False)
    
    # バックアップ作成
    backup_path = mover.create_backup(move_plan)
    print(f"バックアップ: {backup_path}")
    
    # インポートを更新
    print("\n📝 インポートを更新...")
    updater.update_all_files(dry_run=False)
    
    # ファイルを移動
    print("\n📦 ファイルを移動...")
    success_count, errors = mover.execute_moves(move_plan)
    
    print(f"\n結果: {success_count}成功, {len(errors)}エラー")
    
    # 5. 構文検証
    print("\n5️⃣ 移動後の構文を検証...")
    validator = SyntaxValidator(test_src)
    
    # すべてのPythonファイルを検証
    all_py_files = list(test_src.rglob("*.py"))
    syntax_errors = validator.validate_all_files(all_py_files)
    
    if syntax_errors:
        print(f"❌ 構文エラー: {len(syntax_errors)}個")
    else:
        print("✅ すべてのファイルの構文が正常です")
    
    # 6. インポート検証
    print("\n6️⃣ インポートの解決可能性を検証...")
    import_errors = {}
    for py_file in all_py_files:
        unresolved = validator.validate_imports(py_file)
        if unresolved:
            import_errors[py_file] = unresolved
    
    if import_errors:
        print(f"❌ 解決できないインポート: {len(import_errors)}ファイル")
        for file_path, imports in list(import_errors.items())[:3]:
            print(f"  {file_path.name}: {imports}")
    else:
        print("✅ すべてのインポートが解決可能です")
    
    # 7. 実行テスト
    print("\n7️⃣ 移動後のコードを実行テスト...")
    try:
        # main.pyの新しい場所を見つける
        main_files = list(test_src.rglob("main.py"))
        if main_files:
            main_file = main_files[0]
            print(f"実行: {main_file}")
            
            # Pythonパスを調整して実行
            import subprocess
            
            # main.pyを実行可能なスクリプトに変更
            main_content = main_file.read_text()
            # モジュールとしてではなく、直接実行
            exec_content = main_content.replace("from .", "from test_src_phase2.")
            
            # 一時ファイルに書き込んで実行
            temp_main = test_src / "temp_main.py"
            temp_main.write_text(exec_content)
            
            result = subprocess.run(
                [sys.executable, str(temp_main)],
                capture_output=True,
                text=True,
                cwd=str(test_src.parent)
            )
            
            if result.returncode == 0:
                print("✅ 実行成功!")
                print(f"出力: {result.stdout.strip()}")
            else:
                print("❌ 実行エラー")
                print(f"エラー: {result.stderr}")
    except Exception as e:
        print(f"❌ 実行テストエラー: {e}")
    
    # レポート作成
    report_path = mover.save_move_report(move_plan, success_count, errors)
    print(f"\n📄 詳細レポート: {report_path}")
    
    print("\n" + "=" * 60)
    print("✨ Phase 2機能テスト完了!")
    print("=" * 60)

if __name__ == "__main__":
    test_phase2_features()