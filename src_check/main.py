#!/usr/bin/env python3
"""
src_check - 動的インポート版
DFS探索でmain.pyを発見し、順次実行する統合システム
インポート解決の前処理・後処理を含む
"""

import sys
from pathlib import Path

# src_checkのコアモジュールをインポート
sys.path.append(str(Path(__file__).parent))

from core.module_explorer import ModuleExplorer
from core.dynamic_importer import DynamicImporter
from core.result_writer import ResultWriter
from models.check_result import CheckResult
from import_resolver import ImportResolver


def main():
    """統合エントリーポイント"""
    # 基本パスの設定
    src_check_root = Path(__file__).parent
    project_root = src_check_root.parent  # project-cph
    output_dir = src_check_root / "check_result"
    
    # check_resultディレクトリのクリーンアップ
    if output_dir.exists():
        print("🧹 check_resultディレクトリをクリーンアップ中...")
        import shutil
        # ディレクトリ内のファイルを削除（ディレクトリ自体は残す）
        for item in output_dir.iterdir():
            if item.is_file():
                item.unlink()
            elif item.is_dir():
                shutil.rmtree(item)
        print("✅ クリーンアップ完了")
    else:
        # ディレクトリが存在しない場合は作成
        output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # 1. インポート解決（前処理）
        print("=" * 60)
        print("ステップ1: インポートの事前チェック")
        print("=" * 60)
        
        resolver = ImportResolver(project_root)
        pre_check_result = resolver.check_imports()
        
        if pre_check_result.failure_locations:
            print(f"⚠️  {len(pre_check_result.failure_locations)}個の壊れたインポートを検出")
            print("修正を試みます...")
            fix_result = resolver.fix_imports(dry_run=False)
            print(f"✅ {fix_result.fix_policy}")
        else:
            print("✅ すべてのインポートは正常です")
        
        print("\n" + "=" * 60)
        print("ステップ2: 品質チェックの実行")
        print("=" * 60 + "\n")
        
        # 2. DFS探索でmain.pyを発見
        explorer = ModuleExplorer(src_check_root)
        discovered_modules = explorer.discover_main_modules()
        
        if not discovered_modules:
            print("エラー: main.pyファイルが見つかりませんでした。")
            return
        
        # 3. 動的インポートで順次実行
        importer = DynamicImporter(project_root)
        results = []
        critical_errors = []
        
        for module_info in discovered_modules:
            # モジュールの有効性チェック
            if not explorer.validate_module(module_info.path):
                continue
            
            # main関数の存在チェック
            if not importer.validate_main_function(module_info.path):
                continue
            
            # 実行
            try:
                result = importer.import_and_execute(module_info.path, module_info.module_name)
                results.append(result)
                
                # 深刻なエラーチェック
                if "ERROR" in result.title:
                    critical_errors.append({
                        'module': module_info.module_name,
                        'error': result.fix_policy
                    })
                    
            except Exception as e:
                error_msg = f"実行時エラー: {str(e)}"
                critical_errors.append({
                    'module': module_info.module_name,
                    'error': error_msg
                })
                # エラー時もCheckResultを作成
                error_result = CheckResult(
                    title=f"{module_info.module_name}_EXECUTION_ERROR",
                    failure_locations=[],
                    fix_policy=error_msg,
                    fix_example_code=None
                )
                results.append(error_result)
        
        # 4. 結果出力
        writer = ResultWriter(output_dir)
        output_files = writer.write_results(results)
        summary_file = writer.create_summary_report(results)
        
        # 5. 標準出力には深刻なエラーのみ表示
        if critical_errors:
            print("深刻なエラーが発生しました:")
            for error in critical_errors:
                print(f"  - {error['module']}: {error['error']}")
        
        print(f"詳細は {summary_file} を参照してください。")
        
        # 6. インポート解決（後処理）
        print("\n" + "=" * 60)
        print("ステップ3: インポートの事後チェック")
        print("=" * 60)
        
        # ファイル移動などの処理後、再度インポートをチェック
        post_check_result = resolver.check_imports()
        
        if post_check_result.failure_locations:
            print(f"⚠️  処理後に{len(post_check_result.failure_locations)}個の壊れたインポートを検出")
            print("修正を試みます...")
            post_fix_result = resolver.fix_imports(dry_run=False)
            print(f"✅ {post_fix_result.fix_policy}")
            
            # 修正結果も記録
            results.append(post_check_result)
            results.append(post_fix_result)
            
            # 結果を再出力
            writer.write_results(results)
            writer.create_summary_report(results)
        else:
            print("✅ すべてのインポートは正常です")
        
        print("\n" + "=" * 60)
        print("✅ 全処理が完了しました")
        
    except Exception as e:
        print(f"致命的エラー: {str(e)}")
        print(f"詳細は {output_dir} を確認してください。")
        sys.exit(1)


if __name__ == "__main__":
    main()