#!/usr/bin/env python3
"""
クイックインポート修正スクリプト
最も一般的なパターンを迅速に修正
"""
import re
from pathlib import Path
from typing import List, Tuple

# 修正パターンの定義
FIX_PATTERNS = [
    # CLI関連
    (r'from src\.cli\.cli_app import', 'from src.core.cli_app.cli_app import'),
    (r'from src\.cli import', 'from src.core.cli_app.cli_app import'),
    
    # Workflow関連
    (r'from src\.workflow\.workflow_execution_service import', 'from src.core.workflow_execution_svc.workflow_execution_service import'),
    (r'from src\.workflow\.step\.', 'from src.core.workflow.workflow.step.'),
    (r'from src\.workflow\.workflow_result import', 'from src.core.workflow_result.workflow_result import'),
    
    # Services関連（coreに移動されたもの）
    (r'from src\.services\.workflow_execution import', 'from src.core.workflow_execution_svc import'),
    (r'from src\.services\.dependency import', 'from src.core.dependency import'),
    
    # Configuration関連
    (r'from src\.configuration\.resolver\.', 'from src.core.configuration.'),
    (r'from src\.config\.di_config import', 'from src.core.di_config.di_config import'),
    
    # Context関連
    (r'from src\.context\.user_input_parser import', 'from src.core.user_input_parser import'),
    
    # Tests関連
    (r'from src\.tests\.contest_manager import', 'from src.core.contest_mgmt.contest_manager import'),
    (r'from src\.tests\.composite_structure import', 'from src.core.composite_structure.composite_structure import'),
    
    # Handlers/Controllers関連
    (r'from src\.handlers\.', 'from src.core.'),
    (r'from src\.controllers\.', 'from src.core.'),
    (r'from src\.app\.', 'from src.core.'),
]

def fix_imports_in_file(file_path: Path) -> Tuple[bool, List[str]]:
    """ファイル内のインポートを修正"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        changes = []
        
        # パターンマッチで修正
        for pattern, replacement in FIX_PATTERNS:
            matches = re.findall(pattern + r'.*', content)
            if matches:
                content = re.sub(pattern, replacement, content)
                for match in matches:
                    changes.append(f"Fixed: {match}")
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True, changes
            
    except Exception as e:
        return False, [f"Error: {e}"]
    
    return False, []

def main():
    """メイン処理"""
    print("🚀 クイックインポート修正を開始...\n")
    
    src_dir = Path("src")
    python_files = list(src_dir.rglob("*.py"))
    
    fixed_count = 0
    total_changes = 0
    
    for py_file in python_files:
        success, changes = fix_imports_in_file(py_file)
        if success:
            fixed_count += 1
            total_changes += len(changes)
            print(f"✓ {py_file.relative_to(src_dir)} ({len(changes)}箇所)")
            for change in changes[:3]:  # 最初の3つだけ表示
                print(f"  - {change}")
            if len(changes) > 3:
                print(f"  ... 他 {len(changes) - 3}箇所")
    
    print(f"\n📊 完了:")
    print(f"  - {fixed_count}ファイルを修正")
    print(f"  - 合計 {total_changes}箇所を修正")
    
    # 構文チェックの推奨
    if fixed_count > 0:
        print("\n💡 次のコマンドで構文チェックを実行してください:")
        print("   python3 -m compileall src/")

if __name__ == "__main__":
    main()