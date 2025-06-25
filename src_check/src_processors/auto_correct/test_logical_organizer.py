import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from logical_file_organizer import LogicalFileOrganizer, main
from src_check.models.check_result import CheckResult


def test_logical_organizer():
    print("=" * 60)
    print("論理的ファイル整理ツール テスト")
    print("=" * 60)
    
    # CheckResult形式でテスト
    result = main(None)
    
    print(f"\n=== CheckResult ===")
    print(f"整理が必要なファイル数: {len(result.failure_locations)}")
    print(f"\n修正ポリシー:")
    print(result.fix_policy)
    
    if result.fix_example_code:
        print(f"\n期待される構造:")
        print(result.fix_example_code)
    
    # 詳細なシミュレーションも実行
    print("\n" + "=" * 60)
    print("詳細なシミュレーション結果")
    print("=" * 60)
    
    src_dir = "/home/cphelper/project-cph/src"
    organizer = LogicalFileOrganizer(src_dir, dry_run=True)
    file_moves, import_updates = organizer.organize()
    
    # 論理的な整理の例を表示
    print("\n📚 論理的なカテゴリ分類:")
    print("""
    models/         - データモデル、エンティティ、スキーマ
    repositories/   - データアクセス層、永続化
    services/       - ビジネスロジック、ユースケース
    controllers/    - HTTPハンドラー、エンドポイント
    utils/          - 汎用ユーティリティ、ヘルパー
    validators/     - 入力検証、バリデーション
    formatters/     - データ整形、シリアライズ
    parsers/        - パーサー、データ読み込み
    config/         - 設定、環境変数
    constants/      - 定数、列挙型
    infrastructure/ - 外部サービス連携
    adapters/       - アダプター、コネクター
    """)
    
    print("\n✅ テスト完了")
    
    # 実際の移動を実行する例（コメントアウト）
    print("\n💡 実際に移動を実行するには:")
    print("   organizer = LogicalFileOrganizer(src_dir, dry_run=False)")
    print("   file_moves, import_updates = organizer.organize()")
    
    # ロールバックの例
    print("\n🔄 ロールバックするには:")
    print("   rollback_file = Path('.rollback_20240101_120000.json')")
    print("   organizer.rollback(rollback_file)")


if __name__ == "__main__":
    test_logical_organizer()