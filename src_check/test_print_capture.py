from models.check_result import CheckResult, FailureLocation

def main(di_container):
    """print出力キャプチャのテスト用ルール"""
    print("テスト: これはprint出力です")
    print("複数行の出力もテストします")
    print("DIコンテナから設定を取得できました")
    
    # テスト用の失敗を作成
    failures = [
        FailureLocation(file_path="test/dummy1.py", line_number=10),
        FailureLocation(file_path="test/dummy2.py", line_number=20),
    ]
    
    return CheckResult(
        failure_locations=failures,
        fix_policy="テスト用の修正方針です",
        fix_example_code="# 例: print()の代わりにlogger.info()を使用"
    )