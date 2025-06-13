#!/usr/bin/env python3
"""
実用的な品質設定

厳しすぎる制約を実用的なレベルに調整
"""

# 関数型プログラミング品質設定
FUNCTION_QUALITY_CONFIG = {
    # 厳格に維持（エラー）
    'strict_rules': {
        'local_imports': True,           # 関数内インポート禁止
        'global_usage': True,            # グローバル変数禁止
        'circular_imports': True,        # 循環インポート禁止
        'side_effects_in_pure': True,    # 純粋関数での副作用禁止
    },
    
    # 実用的に緩和（警告）
    'practical_limits': {
        'max_function_lines': 25,        # 15→25行に緩和
        'max_file_lines': 300,           # 150→300行に緩和
        'max_function_params': 5,        # 引数数制限
        'max_nesting_depth': 4,          # ネスト深度制限
    },
    
    # 推奨レベル（情報）
    'recommendations': {
        'prefer_dataclass': True,        # dataclass推奨
        'prefer_frozen': True,           # frozen=True推奨
        'avoid_mutable_defaults': True,  # 可変デフォルト引数回避
        'prefer_typing': True,           # 型ヒント推奨
    },
    
    # 例外許可
    'exceptions': {
        'test_files': {
            'max_function_lines': 50,    # テストは長くてもOK
            'allow_side_effects': True,  # テストでは副作用OK
        },
        'legacy_files': [
            # 段階的移行のため一時的に緩和するファイル
            'src/workflow/builder/graph_based_workflow_builder.py',
            'src/workflow/builder/builder_validation.py',
        ],
        'utility_functions': {
            'allow_local_mutable': True, # ローカル変数の変更は許可
            'allow_list_comprehension': True, # リスト内包表記OK
        }
    }
}

# アーキテクチャ品質設定
ARCHITECTURE_CONFIG = {
    'module_structure': {
        'required_modules': [
            'resource_analysis',
            'validation', 
            'graph_ops',
            'execution'
        ],
        'optional_modules': ['debug'],   # デバッグは任意
    },
    
    'dependency_rules': {
        'max_import_depth': 3,           # インポート階層制限
        'allow_sibling_imports': True,   # 同レベルモジュール間OK
        'require_init_files': True,      # __init__.py必須
    }
}