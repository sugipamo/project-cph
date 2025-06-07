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


# オプションの処理
NO_COV=false
HTML=false
PYTEST_ARGS=()

while [[ $# -gt 0 ]]; do
    case $1 in
        --no-cov)
            NO_COV=true
            shift
            ;;
        --html)
            HTML=true
            shift
            ;;
        *)
            PYTEST_ARGS+=("$1")
            shift
            ;;
    esac
done

# 競合オプションのチェック
if [ "$NO_COV" = true ] && [ "$HTML" = true ]; then
    echo "エラー: --no-cov と --html は同時に使用できません"
    echo "HTMLカバレッジレポートを生成するには --html のみを使用してください"
    exit 1
fi

# テストの実行
if [ "$NO_COV" = true ]; then
    # カバレッジなし
    exec pytest "${PYTEST_ARGS[@]}"
elif [ "$HTML" = true ]; then
    # HTMLレポート生成
    exec pytest --cov=src --cov-report=html --cov-report=term "${PYTEST_ARGS[@]}"
else
    # デフォルト: カバレッジ付きテスト実行
    exec pytest --cov=src --cov-report=term-missing "${PYTEST_ARGS[@]}"
fi