"""
fitting モジュールのコンセプトデモ

workflowとfittingの責務分離を示すシンプルな例
"""

def demonstrate_separation_concept():
    """責務分離のコンセプトデモ"""
    
    print("=== Workflow と Fitting の責務分離 ===")
    print()
    
    print("【BEFORE: 混在していた責務】")
    print("- workflowが実環境チェックも担当")
    print("- operationsへの依存が混在")
    print("- 責務が不明確")
    print()
    
    print("【AFTER: 分離された責務】")
    print()
    
    print("1. workflow モジュール:")
    print("   - ユーザー指定のrequestを純粋に生成")
    print("   - operationsに依存しない")
    print("   - 例: json_steps → [mkdir_request, copy_request, ...]")
    print()
    
    print("2. fitting モジュール:")
    print("   - operations経由で実環境の状態確認")
    print("   - ワークフロー要求と実環境の差異分析")
    print("   - 必要な事前準備requestの生成・実行")
    print("   - 例: フォルダが存在しない → mkdir_preparation_request")
    print()
    
    print("【統合フロー】")
    print("1. workflow: ユーザー要求 → pure requests")
    print("2. fitting: operations → 環境確認 → 差異分析")
    print("3. fitting: 事前準備requests生成・実行")
    print("4. main: workflow requests実行")
    print()
    
    print("【具体例】")
    print("ユーザー要求: ./project/src/main.py をコピー")
    print()
    print("workflow:")
    print("  → copy_request('./template/main.py', './project/src/main.py')")
    print("  （operationsを使わない純粋な生成）")
    print()
    print("fitting:")
    print("  → operations.file_driver.exists('./project/src') → False")
    print("  → mkdir_request('./project/src') を事前準備として生成・実行")
    print("  → 環境が整った状態でworkflowを実行可能に")
    print()
    
    print("✅ 責務分離完了")
    print("✅ workflow: 純粋・テスタブル")
    print("✅ fitting: 実環境との橋渡し")

def demonstrate_api_design():
    """API設計のデモ"""
    print()
    print("=== API設計 ===")
    print()
    
    print("# workflow (純粋)")
    print("builder = GraphBasedWorkflowBuilder(controller, operations)")
    print("graph, errors, warnings = builder.build_graph_from_json_steps(json_steps)")
    print("# → operationsを渡すが、内部では使わない設計に変更予定")
    print()
    
    print("# fitting (operations使用)")
    print("fitting = PreparationExecutor(operations)")
    print("result = fitting.fit_workflow_to_environment(graph)")
    print("# → operations経由で環境確認・準備実行")
    print()
    
    print("# 統合使用例")
    print("if result['preparation_needed']:")
    print("    print(f'事前準備完了: {result[\"successful_preparations\"]}件')")
    print("# 準備が整った状態でworkflow実行")
    print("workflow_results = graph.execute_sequential(driver)")

if __name__ == "__main__":
    demonstrate_separation_concept()
    demonstrate_api_design()