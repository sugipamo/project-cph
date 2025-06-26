#!/bin/bash

# src_checkを実行するスクリプト
# cphelperディレクトリまたはproject-cphディレクトリから実行可能

set -e  # エラー時に終了

# 実行ディレクトリの確認と調整
if [[ -d "project-cph" ]]; then
    # cphelperディレクトリから実行された場合
    echo "📂 cphelperディレクトリから実行を検出"
    cd project-cph
elif [[ -d "src_check" ]]; then
    # project-cphディレクトリから実行された場合
    echo "📂 project-cphディレクトリから実行を検出"
    # そのまま
else
    echo "エラー: cphelperディレクトリまたはproject-cphディレクトリから実行してください"
    echo "（project-cphまたはsrc_checkディレクトリが見つかりません）"
    exit 1
fi

# src_checkディレクトリの存在確認
if [[ ! -d "src_check" ]]; then
    echo "エラー: src_checkディレクトリが見つかりません"
    exit 1
fi

# src_check/main.pyの存在確認
if [[ ! -f "src_check/main.py" ]]; then
    echo "エラー: src_check/main.pyが見つかりません"
    exit 1
fi

echo "🔍 src_checkを実行します..."
echo "📂 実行ディレクトリ: $(pwd)"
echo ""

# PYTHONPATHをクリアして、src_checkディレクトリから実行
cd src_check
# 完全にPYTHONPATHをクリアして、絶対パス指定で実行
unset PYTHONPATH
export PYTHONPATH="$(pwd)"
/usr/bin/python3 "$(pwd)/main.py" "$@"

# 元のディレクトリに戻る
cd ..

echo ""
echo "✅ src_checkの実行が完了しました"
echo "📋 詳細結果は src_check/src_check_result/ を確認してください"