#!/bin/bash

# 壊れたインポート修正ツールを実行するスクリプト
# cphelperディレクトリまたはproject-cphディレクトリから実行可能

set -e  # エラー時に終了

# 実行ディレクトリの確認と調整
if [[ -d "project-cph" ]]; then
    # cphelperディレクトリから実行された場合
    echo "📂 cphelperディレクトリから実行を検出"
    cd project-cph
elif [[ -d "scripts" && -f "scripts/broken_import_fixer.py" ]]; then
    # project-cphディレクトリから実行された場合
    echo "📂 project-cphディレクトリから実行を検出"
    # そのまま
else
    echo "エラー: cphelperディレクトリまたはproject-cphディレクトリから実行してください"
    echo "（project-cphまたはscripts/broken_import_fixer.pyが見つかりません）"
    exit 1
fi

# broken_import_fixer.pyの存在確認
if [[ ! -f "scripts/broken_import_fixer.py" ]]; then
    echo "エラー: scripts/broken_import_fixer.pyが見つかりません"
    exit 1
fi

echo "🔧 壊れたインポート修正ツールを実行します..."
echo "📂 実行ディレクトリ: $(pwd)"
echo ""

# 引数がない場合はhelpを表示
if [[ $# -eq 0 ]]; then
    echo "使用方法:"
    echo "  $0 find              # 壊れたインポートを検索"
    echo "  $0 fix               # 壊れたインポートを修正"
    echo "  $0 analyze           # プロジェクトの分析"
    echo ""
    echo "詳細なオプションを確認:"
    python3 scripts/broken_import_fixer.py --help
    exit 0
fi

# 壊れたインポート修正ツールを実行（PYTHONPATHを設定）
export PYTHONPATH="$(pwd):$PYTHONPATH"
python3 scripts/broken_import_fixer.py "$@"

echo ""
echo "✅ 壊れたインポート修正ツールの実行が完了しました"