#!/bin/bash

# テストカバレッジレポート付きでテストを実行
# 使用方法:
#   ./test.sh                    # 全テスト実行（カバレッジ付き）
#   ./test.sh -k test_name       # 特定のテスト実行
#   ./test.sh --no-cov          # カバレッジなしで実行
#   ./test.sh --html             # HTMLカバレッジレポート生成

if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "使用方法:"
    echo "  ./test.sh                    # 全テスト実行（カバレッジ付き）"
    echo "  ./test.sh -k test_name       # 特定のテスト実行"
    echo "  ./test.sh --no-cov          # カバレッジなしで実行"
    echo "  ./test.sh --html             # HTMLカバレッジレポート生成"
    echo "  ./test.sh --help             # このヘルプを表示"
    exit 0
fi

# カバレッジなしオプション
if [ "$1" = "--no-cov" ]; then
    shift
    exec pytest "$@"
fi

# HTMLレポート生成オプション
if [ "$1" = "--html" ]; then
    shift
    exec pytest --cov=src --cov-report=html --cov-report=term "$@"
fi

# デフォルト: カバレッジ付きテスト実行
if [ $# -eq 0 ]; then
    exec pytest --cov=src --cov-report=term-missing
else
    exec pytest --cov=src --cov-report=term-missing "$@"
fi