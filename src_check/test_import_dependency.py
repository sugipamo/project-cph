"""import_dependency_reorganizerのテスト"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))
from src_processors.auto_correct.import_dependency_reorganizer.main import main

if __name__ == "__main__":
    result = main()
    print(f"CheckResult:")
    print(f"  failure_locations: {len(result.failure_locations)}")
    print(f"  fix_policy: {result.fix_policy[:100]}...")
    print(f"  fix_example_code: {result.fix_example_code}")