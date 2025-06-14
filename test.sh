#!/bin/bash

# テストカバレッジレポート付きでテストを実行
# 使用方法:
#   ./test.sh                    # 全テスト実行（カバレッジ付き）
#   ./test.sh -k test_name       # 特定のテスト実行
#   ./test.sh --no-cov          # カバレッジなしで実行
#   ./test.sh --html             # HTMLカバレッジレポート生成
#   ./test.sh --no-ruff          # ruffスキップ
#   ./test.sh --check-only       # cargo check相当（テストなし）

if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "使用方法:"
    echo "  ./test.sh                    # 全テスト実行（カバレッジ付き）"
    echo "  ./test.sh -k test_name       # 特定のテスト実行"
    echo "  ./test.sh --no-cov          # カバレッジなしで実行"
    echo "  ./test.sh --html             # HTMLカバレッジレポート生成"
    echo "  ./test.sh --no-ruff          # ruffスキップ"
    echo "  ./test.sh --check-only       # cargo check相当（テストなし）"
    echo "  ./test.sh --help             # このヘルプを表示"
    exit 0
fi


# オプションの処理
NO_COV=false
HTML=false
NO_RUFF=false
CHECK_ONLY=false
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
        --no-ruff)
            NO_RUFF=true
            shift
            ;;
        --check-only)
            CHECK_ONLY=true
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

# コード品質チェック（ruff）
if [ "$NO_RUFF" = false ]; then
    echo "=== コード品質チェック（ruff）==="
    if command -v ruff &> /dev/null; then
        echo "ruffでコード品質をチェック中..."
        ruff check --fix --unsafe-fixes
        ruff_exit_code=$?
        
        if [ $ruff_exit_code -ne 0 ]; then
            echo "警告: ruffで修正できない品質問題が残っています"
            echo "詳細を確認してください: ruff check"
        else
            echo "✓ コード品質チェック完了"
        fi
        
        # 汎用名チェック
        if [ -f "scripts/check_generic_names.py" ]; then
            echo "🔍 汎用名チェック中..."
            if ! python3 scripts/check_generic_names.py src/; then
                echo "汎用名の修正が必要です"
            fi
        fi
        
        # 実用的品質チェック（関数型プログラミングの実用的な適用）
        if [ -f "scripts/practical_quality_check.py" ]; then
            echo "🎯 実用的品質チェック中..."
            if ! python3 scripts/practical_quality_check.py; then
                echo "品質基準の修正が必要です"
            fi
        elif [ -f "scripts/functional_quality_check.py" ]; then
            echo "🎯 関数型品質チェック中..."
            if ! python3 scripts/functional_quality_check.py src/; then
                echo "関数型品質基準の修正が必要です"
            fi
        fi
        
        # アーキテクチャ品質チェック
        if [ -f "scripts/architecture_quality_check.py" ]; then
            echo "🏗️  アーキテクチャ品質チェック中..."
            if ! python3 scripts/architecture_quality_check.py src/; then
                echo "アーキテクチャ改善が必要です"
            fi
        fi
        
        echo ""
    else
        echo "警告: ruffがインストールされていません"
        echo "インストール: pip install ruff"
        echo ""
    fi
fi

# check-onlyモード（cargo check相当）
if [ "$CHECK_ONLY" = true ]; then
    echo "=== 高速チェック（cargo check相当）==="
    
    # 2. 型チェック（mypy）
    echo ""
    echo "🔍 型チェック中..."
    if command -v mypy &> /dev/null; then
        if ! mypy src/ --no-error-summary --quiet 2>/dev/null; then
            echo "❌ 型エラーが見つかりました"
            echo "詳細:"
            mypy src/ --show-error-codes | head -10
            exit 1
        else
            echo "✓ 型チェック完了"
        fi
    else
        echo "⚠️  mypyがインストールされていません（推奨）"
        echo "インストール: pip install mypy"
    fi

    # 3. 基本構文チェック
    echo ""
    echo "📝 構文チェック中..."
    if python3 -c "
import ast
import glob
import sys

errors = []
for file in glob.glob('src/**/*.py', recursive=True):
    try:
        with open(file, 'r', encoding='utf-8') as f:
            ast.parse(f.read(), filename=file)
    except SyntaxError as e:
        errors.append(f'{file}:{e.lineno}: {e.msg}')
    except Exception as e:
        errors.append(f'{file}: {e}')

if errors:
    print('❌ 構文エラー:')
    for error in errors[:10]:  # 最初の10個のみ
        print(f'  {error}')
    sys.exit(1)
else:
    print('✓ 構文チェック完了')
"; then
        echo ""
        echo "🎉 チェック完了（cargo check相当）"
        echo "詳細テスト: ./test.sh"
        exit 0
    else
        echo "💥 構文エラーが見つかりました"
        exit 1
    fi
fi

# テストの実行
echo "=== テスト実行 ==="
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