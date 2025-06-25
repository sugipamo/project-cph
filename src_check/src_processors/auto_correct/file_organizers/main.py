"""
ファイル整理自動修正メインモジュール

src_check/main.pyから動的に読み込まれ、src配下のファイルを
論理的な構造に自動整理します。
"""
import sys
from pathlib import Path
from typing import Dict, Any, Optional

sys.path.append(str(Path(__file__).parent.parent.parent.parent))
from src_check.models.check_result import CheckResult, FailureLocation

# 同じディレクトリのモジュールをインポート
sys.path.append(str(Path(__file__).parent))
from file_splitter import FileSplitter
from structure_organizer import StructureOrganizer
from logical_file_organizer import LogicalFileOrganizer
try:
    from smart_organizer import SmartOrganizer
    HAS_SMART_ORGANIZER = True
except ImportError:
    HAS_SMART_ORGANIZER = False


def main() -> CheckResult:
    """
    ファイル整理のメインエントリーポイント
        
    Returns:
        CheckResult: チェック結果
    """
    project_root = Path(__file__).parent.parent.parent.parent.parent
    src_dir = project_root / 'src'
    
    # 設定を取得（将来的にはDIコンテナから）
    config = {
        'mode': 'logical',  # 'split', 'structure', 'logical', 'smart'
        'dry_run': True,
        'single_function': True,
        'single_class': True
    }
    
    print(f"🔍 ファイル整理解析を開始: {src_dir}")
    print(f"モード: {config['mode']}")
    
    try:
        if config['mode'] == 'split':
            # 1ファイル1関数/クラスに分割
            return _run_file_splitter(src_dir, config, print)
            
        elif config['mode'] == 'structure':
            # 循環参照チェックと構造整理
            return _run_structure_organizer(src_dir, config, print)
            
        elif config['mode'] == 'logical':
            # 論理的なフォルダ構造に整理
            return _run_logical_organizer(src_dir, config, print)
            
        elif config['mode'] == 'smart':
            # 依存関係に基づくスマート整理
            if HAS_SMART_ORGANIZER:
                return _run_smart_organizer(src_dir, config, print)
            else:
                return CheckResult(
                    failure_locations=[],
                    fix_policy="SmartOrganizerは利用できません（networkxが必要です）",
                    fix_example_code=None
                )
            
        else:
            return CheckResult(
                failure_locations=[],
                fix_policy=f"不明なモード: {config['mode']}",
                fix_example_code=None
            )
            
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        return CheckResult(
            failure_locations=[],
            fix_policy=f"ファイル整理中にエラーが発生しました: {str(e)}",
            fix_example_code=None
        )


def _run_file_splitter(src_dir: Path, config: Dict[str, Any], print) -> CheckResult:
    """ファイル分割モードの実行"""
    splitter = FileSplitter(
        str(src_dir),
        single_function_per_file=config['single_function'],
        single_class_per_file=config['single_class']
    )
    
    results = splitter.analyze_and_split_project(dry_run=config['dry_run'])
    
    print(f"  解析したファイル数: {results['files_analyzed']}")
    print(f"  分割対象ファイル数: {results['files_to_split']}")
    
    failure_locations = []
    for plan in results.get('split_plans', []):
        failure_locations.append(FailureLocation(
            file_path=plan['source'],
            line_number=0
        ))
    
    if failure_locations:
        return CheckResult(
            failure_locations=failure_locations,
            fix_policy=f"{len(failure_locations)}個のファイルが1ファイル1関数/1クラスの原則に違反しています。",
            fix_example_code="# 分割後:\n# utils/function1.py\n# utils/function2.py"
        )
    else:
        return CheckResult(
            failure_locations=[],
            fix_policy="すべてのファイルが原則に従っています。",
            fix_example_code=None
        )


def _run_structure_organizer(src_dir: Path, config: Dict[str, Any], print) -> CheckResult:
    """構造整理モードの実行"""
    organizer = StructureOrganizer(str(src_dir))
    organizer.analyze_project()
    
    if organizer.check_issues():
        failure_locations = []
        
        for ref1, ref2 in organizer.circular_references:
            failure_locations.append(FailureLocation(
                file_path=ref1,
                line_number=0
            ))
        
        for module, path in organizer.delayed_imports:
            failure_locations.append(FailureLocation(
                file_path=path,
                line_number=0
            ))
        
        return CheckResult(
            failure_locations=failure_locations,
            fix_policy="循環参照または遅延インポートを解決してください。",
            fix_example_code="# Protocolを使用した循環参照の解決例"
        )
    
    ideal_structure = organizer.determine_ideal_structure()
    
    if ideal_structure:
        failure_locations = []
        move_steps = organizer.generate_move_plan(ideal_structure)
        
        for step in move_steps:
            failure_locations.append(FailureLocation(
                file_path=str(step.source),
                line_number=0
            ))
        
        return CheckResult(
            failure_locations=failure_locations,
            fix_policy=f"{len(move_steps)}個のファイルの再配置が推奨されます。",
            fix_example_code="# src/\n#   domain/\n#   application/\n#   infrastructure/"
        )
    
    return CheckResult(
        failure_locations=[],
        fix_policy="現在の構造は適切です。",
        fix_example_code=None
    )


def _run_logical_organizer(src_dir: Path, config: Dict[str, Any], print) -> CheckResult:
    """論理的整理モードの実行"""
    organizer = LogicalFileOrganizer(str(src_dir), dry_run=config['dry_run'])
    file_moves, import_updates = organizer.organize()
    
    failure_locations = []
    for move in file_moves:
        failure_locations.append(FailureLocation(
            file_path=str(move.source),
            line_number=0
        ))
    
    if failure_locations:
        return CheckResult(
            failure_locations=failure_locations,
            fix_policy=(
                f"{len(file_moves)}個のファイルを論理的なフォルダ構造に再配置します。\n"
                f"影響を受けるインポート: {len(import_updates)}箇所"
            ),
            fix_example_code=(
                "# 整理後:\n"
                "# models/\n"
                "# repositories/\n"
                "# services/\n"
                "# utils/"
            )
        )
    
    return CheckResult(
        failure_locations=[],
        fix_policy="ファイル構造は既に論理的に整理されています。",
        fix_example_code=None
    )


def _run_smart_organizer(src_dir: Path, config: Dict[str, Any], print) -> CheckResult:
    """スマート整理モードの実行"""
    organizer = SmartOrganizer(str(src_dir))
    organizer.analyze_codebase()
    
    plan = organizer.generate_organization_plan()
    issues = organizer.validate_plan(plan)
    
    print(f"  発見されたモジュール: {len(plan.modules)}")
    print(f"  リスク評価: {plan.risk_assessment}")
    
    if issues:
        print("  検証で問題が発見されました:")
        for issue in issues:
            print(f"    - {issue}")
    
    failure_locations = []
    for module in plan.modules:
        unique_files = set(e.file_path for e in module.elements)
        for file_path in unique_files:
            failure_locations.append(FailureLocation(
                file_path=str(file_path),
                line_number=0
            ))
    
    if failure_locations:
        return CheckResult(
            failure_locations=failure_locations,
            fix_policy=(
                f"{len(plan.modules)}個のモジュールへの再編成を推奨します。"
                f"凝集度に基づいた論理的なグループ化により保守性が向上します。"
            ),
            fix_example_code="# 凝集度の高いモジュール構造"
        )
    
    return CheckResult(
        failure_locations=[],
        fix_policy="現在のファイル構造は適切です。",
        fix_example_code=None
    )


if __name__ == "__main__":
    # テスト実行
    result = main()
    print(f"\nCheckResult: {len(result.failure_locations)} files need organization")