"""
Phase 3機能のテスト
エラーハンドリング、ログ、設定ファイル機能の統合テスト
"""

import sys
import json
from pathlib import Path
import shutil

# プロトタイプのパスを追加
sys.path.insert(0, "src_check/src_processors/auto_correct/import_dependency_reorganizer")

from main_v2 import main
from config import ReorganizerConfig, save_example_config

def test_phase3_features():
    """Phase 3機能の統合テスト"""
    
    print("🔧 Phase 3機能テスト開始")
    print("=" * 60)
    
    # テスト用設定ファイルを作成
    test_config_path = Path("test_reorganizer_config.json")
    
    config_data = {
        "max_file_count": 10,
        "max_depth": 3,
        "execute_mode": False,
        "dry_run": True,
        "exclude_patterns": ["__pycache__", "*.pyc"],
        "log_level": "DEBUG",
        "log_to_file": True,
        "verbose": True,
        "depth_folder_mapping": {
            "0": "",
            "1": "foundation",
            "2": "business",
            "3": "application"
        },
        "validate_syntax": True,
        "validate_imports": True
    }
    
    with open(test_config_path, 'w') as f:
        json.dump(config_data, f, indent=2)
    
    print(f"✅ テスト設定ファイル作成: {test_config_path}")
    
    # テスト用プロジェクトを再作成
    test_src = Path("test_src_phase3")
    if test_src.exists():
        shutil.rmtree(test_src)
    test_src.mkdir()
    
    # より複雑なプロジェクト構造を作成（エラーケースを含む）
    # 正常なファイル
    (test_src / "__init__.py").write_text("")
    
    (test_src / "config.py").write_text("""
# 設定ファイル
DEBUG = True
API_KEY = "secret"
""")
    
    (test_src / "logger.py").write_text("""
# ロガー
from .config import DEBUG

def log(message):
    if DEBUG:
        print(f"LOG: {message}")
""")
    
    # 循環依存を作成
    (test_src / "module_a.py").write_text("""
# モジュールA
from .module_b import function_b

def function_a():
    return function_b() + "_a"
""")
    
    (test_src / "module_b.py").write_text("""
# モジュールB
from .module_a import function_a

def function_b():
    return "b"
    
def function_b2():
    return function_a() + "_b2"
""")
    
    # 構文エラーのあるファイル
    (test_src / "broken_syntax.py").write_text("""
# 構文エラー
def broken(:
    return "broken"
""")
    
    # 存在しないモジュールをインポート
    (test_src / "import_error.py").write_text("""
# インポートエラー
from .non_existent import something

def use_something():
    return something()
""")
    
    print("✅ テストプロジェクト作成完了（エラーケース含む）")
    
    # 1. 設定ファイルからの読み込みテスト
    print("\n1️⃣ 設定ファイル読み込みテスト")
    try:
        config = ReorganizerConfig.from_file(test_config_path)
        print(f"  ✅ 設定読み込み成功: max_file_count={config.max_file_count}")
        
        # 設定の検証
        errors = config.validate()
        if errors:
            print(f"  ❌ 設定エラー: {errors}")
        else:
            print("  ✅ 設定検証成功")
    except Exception as e:
        print(f"  ❌ 設定読み込みエラー: {e}")
    
    # 2. エラーハンドリングテスト（循環依存）
    print("\n2️⃣ エラーハンドリングテスト")
    
    # 一時的にsrcをtest_srcに変更
    original_main_code = Path("src_check/src_processors/auto_correct/import_dependency_reorganizer/main_v2.py").read_text()
    modified_code = original_main_code.replace('src_root = project_root / "src"', 'src_root = project_root / "test_src_phase3"')
    
    temp_main = Path("src_check/src_processors/auto_correct/import_dependency_reorganizer/main_v2_temp.py")
    temp_main.write_text(modified_code)
    
    # インポートパスを調整
    sys.path.insert(0, str(temp_main.parent))
    from main_v2_temp import main as main_temp
    
    result = main_temp(config)
    print(f"  結果: {result.fix_policy}")
    
    if result.fix_example_code:
        print("\n  エラーレポート:")
        print("  " + "\n  ".join(result.fix_example_code.split("\n")[:10]))
    
    # 3. ログ機能テスト
    print("\n3️⃣ ログ機能テスト")
    log_dir = Path("src_check/src_processors/auto_correct/import_dependency_reorganizer/logs")
    if log_dir.exists():
        log_files = list(log_dir.glob("*.log"))
        if log_files:
            print(f"  ✅ ログファイル生成: {len(log_files)}個")
            
            # 最新のログファイルの内容を確認
            latest_log = max(log_files, key=lambda p: p.stat().st_mtime)
            print(f"  📄 最新ログ: {latest_log.name}")
            
            # 最初の数行を表示
            with open(latest_log, 'r') as f:
                lines = f.readlines()[:5]
                for line in lines:
                    print(f"    {line.strip()}")
        else:
            print("  ❌ ログファイルが生成されていません")
    
    # 4. 循環依存を無視する設定でテスト
    print("\n4️⃣ 循環依存無視モードテスト")
    config.ignore_circular_deps = True
    result = main_temp(config)
    print(f"  結果: {result.fix_policy}")
    
    # 5. 実行モードテスト（構文エラーを除外）
    print("\n5️⃣ 実行モードテスト（エラーファイル除外）")
    
    # エラーファイルを削除
    (test_src / "broken_syntax.py").unlink()
    (test_src / "import_error.py").unlink()
    
    config.execute_mode = True
    config.dry_run = False
    config.max_file_count = 50  # 制限を緩和
    
    result = main_temp(config)
    print(f"  結果: {result.fix_policy}")
    
    # 6. カスタムフォルダ名テスト
    print("\n6️⃣ カスタムフォルダ名マッピング確認")
    
    # foundation/business/applicationフォルダが作成されたか確認
    for folder in ["foundation", "business", "application"]:
        folder_path = test_src / folder
        if folder_path.exists():
            print(f"  ✅ {folder}フォルダ作成確認")
            # 中身を確認
            py_files = list(folder_path.rglob("*.py"))
            if py_files:
                print(f"    含まれるファイル: {[f.name for f in py_files[:3]]}")
    
    # 7. 統計情報の確認
    print("\n7️⃣ 実行統計")
    
    # JSONログファイルを確認
    json_logs = list(log_dir.glob("*.json")) if log_dir.exists() else []
    if json_logs:
        latest_json = max(json_logs, key=lambda p: p.stat().st_mtime)
        with open(latest_json, 'r') as f:
            log_data = json.load(f)
        
        print(f"  総イベント数: {log_data.get('event_count', 0)}")
        print(f"  実行時間: {log_data.get('total_duration', 0):.2f}秒")
        
        # レベル別カウント
        level_counts = {}
        for event in log_data.get('events', []):
            level = event.get('level')
            level_counts[level] = level_counts.get(level, 0) + 1
        
        print("  ログレベル別:")
        for level, count in sorted(level_counts.items()):
            print(f"    {level}: {count}件")
    
    # クリーンアップ
    temp_main.unlink()
    test_config_path.unlink()
    
    print("\n" + "=" * 60)
    print("✨ Phase 3機能テスト完了!")
    print("=" * 60)

if __name__ == "__main__":
    test_phase3_features()