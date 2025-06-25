#!/usr/bin/env python3
"""
品質チェックツール - DRY RUN版（実際の修正は行わない）

実際に修正を行いたい場合は main.py を使用してください。
"""
import os
import sys
import subprocess

# 環境変数でDRY_RUNモードを設定
os.environ['SRC_CHECK_DRY_RUN'] = '1'

# main.pyを実行
if __name__ == "__main__":
    print("=" * 80)
    print("DRY RUNモード - ファイルは修正されません")
    print("実際に修正する場合は: python3 src_check/main.py")
    print("=" * 80)
    print()
    
    # main.pyのパスを取得
    current_dir = os.path.dirname(os.path.abspath(__file__))
    main_path = os.path.join(current_dir, 'main.py')
    
    # 引数をそのまま渡してmain.pyを実行
    subprocess.run([sys.executable, main_path] + sys.argv[1:])