"""
メインエントリーポイント（改良版）
エラーハンドリング、ログ、設定ファイル対応
"""

import sys
import os
import json
from pathlib import Path
import time
from datetime import datetime
from typing import Optional, Dict, List, Tuple

# src_checkディレクトリをsys.pathに追加
src_check_dir = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(src_check_dir))

from models.check_result import CheckResult, FailureLocation

# 現在のディレクトリをパスに追加
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from simple_import_analyzer import SimpleImportAnalyzer
from dependency_calculator import DependencyCalculator
from import_updater_v3 import ImportUpdaterV3
from file_mover import FileMover
from syntax_validator import SyntaxValidator
from config import ReorganizerConfig, create_default_config
from logger import setup_logger, get_logger
from graph_visualizer import DependencyGraphVisualizer
from errors import (
    ErrorCollector, CircularDependencyError, ImportAnalysisError,
    ImportUpdateError, FileMoveError, ValidationError, ConfigurationError
)

def main(config: Optional[ReorganizerConfig] = None, 
         config_file: Optional[Path] = None) -> CheckResult:
    """
    インポート依存関係ベースフォルダ構造整理（改良版）
    
    Args:
        config: 設定オブジェクト
        config_file: 設定ファイルパス
    """
    start_time = time.time()
    
    # 設定の読み込み
    if config is None:
        if config_file and config_file.exists():
            try:
                config = ReorganizerConfig.from_file(config_file)
            except Exception as e:
                return CheckResult(
                    failure_locations=[FailureLocation(file_path="config", line_number=0)],
                    fix_policy=f"設定ファイル読み込みエラー: {str(e)}",
                    fix_example_code=None
                )
        else:
            config = create_default_config()
    
    # 設定の検証
    config_errors = config.validate()
    if config_errors:
        return CheckResult(
            failure_locations=[FailureLocation(file_path="config", line_number=0)],
            fix_policy=f"設定エラー: {'; '.join(config_errors)}",
            fix_example_code=None
        )
    
    # ログの設定
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = None
    if config.log_to_file:
        log_dir = Path(__file__).parent / "logs"
        log_file = log_dir / config.log_file_name.format(timestamp=timestamp)
    
    logger = setup_logger(
        log_level=config.log_level,
        log_file=log_file,
        enable_console=True
    )
    
    # エラーコレクター
    error_collector = ErrorCollector()
    
    logger.info("依存関係ベースフォルダ構造整理を開始", config=config.__dict__)
    
    try:
        # プロジェクトルート設定
        project_root = Path(__file__).parent.parent.parent.parent.parent
        src_root = project_root / "src"
        
        logger.info(f"プロジェクトルート: {project_root}")
        logger.info(f"解析対象: {src_root}")
        
        if not src_root.exists():
            error = ConfigurationError("src_root", "src/ディレクトリが見つかりません")
            error_collector.add_error(error)
            return _create_error_result(error_collector, start_time)
        
        # Phase 1: ファイル収集と解析
        phase_start = time.time()
        logger.log_phase_start("Phase 1", "ファイル収集と依存関係解析")
        
        python_files = []
        for py_file in src_root.rglob("*.py"):
            if not config.should_exclude_file(py_file):
                python_files.append(py_file)
        
        file_count = len(python_files)
        logger.info(f"発見されたPythonファイル数: {file_count}")
        
        # ファイル数制限チェック
        if file_count > config.max_file_count:
            error = ConfigurationError(
                "file_count",
                f"ファイル数が制限を超えています ({file_count} > {config.max_file_count})"
            )
            error_collector.add_error(error)
            return _create_error_result(error_collector, start_time)
        
        if file_count == 0:
            logger.warning("Pythonファイルが見つかりませんでした")
            return CheckResult(
                failure_locations=[],
                fix_policy="Pythonファイルが見つかりませんでした",
                fix_example_code=None
            )
        
        # インポート解析
        analyzer = SimpleImportAnalyzer(src_root)
        
        for py_file in python_files:
            try:
                analyzer.analyze_file(py_file)
                imports = analyzer.file_imports.get(py_file, [])
                logger.log_import_analysis(py_file, len(imports), imports)
            except Exception as e:
                error = ImportAnalysisError(py_file, e)
                error_collector.add_error(error)
                if config.stop_on_first_error:
                    return _create_error_result(error_collector, start_time)
        
        # 依存関係計算
        calculator = DependencyCalculator(analyzer)
        
        # 循環依存チェック
        circular_deps = calculator.detect_circular_dependencies()
        if circular_deps and not config.ignore_circular_deps:
            error = CircularDependencyError(circular_deps)
            error_collector.add_error(error)
            return _create_error_result(error_collector, start_time)
        elif circular_deps:
            for cycle in circular_deps:
                error_collector.add_warning(
                    "circular_dependency",
                    f"循環依存を無視: {' → '.join(cycle)}",
                    {"cycle": cycle}
                )
        
        # 深度計算
        depth_map = calculator.calculate_dependency_depths(max_depth=config.max_depth)
        
        for file_path, depth in depth_map.items():
            module_name = analyzer.path_to_module_name(file_path)
            deps = analyzer.get_dependencies(file_path)
            logger.log_dependency_depth(module_name, depth, deps)
        
        logger.log_phase_end("Phase 1", True, time.time() - phase_start)
        
        # Phase 2: 移動計画作成
        phase_start = time.time()
        logger.log_phase_start("Phase 2", "移動計画の作成")
        
        move_plan = _create_move_plan_v2(depth_map, src_root, config)
        logger.log_move_plan(move_plan)
        
        logger.log_phase_end("Phase 2", True, time.time() - phase_start)
        
        # グラフ生成（オプション）
        if hasattr(config, 'generate_graph') and config.generate_graph:
            phase_start = time.time()
            logger.log_phase_start("Graph Generation", "依存関係グラフの生成")
            
            visualizer = DependencyGraphVisualizer(analyzer, calculator)
            graph_dir = Path(__file__).parent / "graphs"
            
            try:
                # 各種形式でグラフを生成
                visualizer.generate_dot(graph_dir / "dependency_graph.dot", depth_map)
                visualizer.generate_mermaid(graph_dir / "dependency_graph.md", depth_map)
                visualizer.generate_json_graph(graph_dir / "dependency_graph.json", depth_map)
                visualizer.generate_ascii_tree(graph_dir / "dependency_tree.txt")
                visualizer.generate_summary_report(graph_dir / "dependency_report.md")
                
                # HTMLビューアも生成
                _generate_html_viewer(graph_dir / "dependency_graph.json", 
                                    graph_dir / "graph_viewer.html")
                
                logger.info("グラフ生成完了", output_dir=str(graph_dir))
                logger.log_phase_end("Graph Generation", True, time.time() - phase_start)
            except Exception as e:
                logger.error(f"グラフ生成エラー: {str(e)}")
                error_collector.add_warning("graph_generation", str(e))
        
        # 実行モードの場合
        if config.execute_mode and not config.dry_run and move_plan:
            return _execute_reorganization(
                src_root, move_plan, config, logger, error_collector, start_time
            )
        
        # シミュレーションモード
        total_time = time.time() - start_time
        
        if error_collector.has_errors():
            return _create_error_result(error_collector, start_time)
        
        return CheckResult(
            failure_locations=[],
            fix_policy=f"シミュレーション完了: {len(move_plan)}ファイルの移動を計画 (実行時間: {total_time:.2f}秒)",
            fix_example_code=f"実行するには config.execute_mode=True を設定してください\n{error_collector.format_report()}"
        )
        
    except Exception as e:
        logger.critical(f"予期しないエラー: {str(e)}", error_type=type(e).__name__)
        return CheckResult(
            failure_locations=[FailureLocation(file_path="system", line_number=0)],
            fix_policy=f"システムエラー: {str(e)}",
            fix_example_code=None
        )
    finally:
        # ログを保存
        if config.log_to_file and log_file:
            logger.save_execution_log(log_file.with_suffix('.json'))
        
        # 統計情報を出力
        stats = logger.get_statistics()
        logger.info("実行統計", **stats)

def _create_move_plan_v2(depth_map: Dict[Path, int], src_root: Path, 
                        config: ReorganizerConfig) -> Dict[Path, Path]:
    """改良版移動計画作成"""
    move_plan = {}
    logger = get_logger()
    
    for file_path, depth in depth_map.items():
        # 深度0または保持対象ファイルはスキップ
        if depth == 0 or file_path.name in config.preserve_structure_for:
            continue
        
        # フォルダ名を決定
        folder_name = config.get_custom_folder_name(file_path.stem)
        if not folder_name:
            folder_name = file_path.stem
        
        # 深度に基づくパスを構築
        depth_folder = config.get_folder_for_depth(depth)
        if depth_folder:
            new_path = src_root / depth_folder / folder_name / file_path.name
        else:
            new_path = src_root / folder_name / file_path.name
        
        if new_path != file_path:
            move_plan[file_path] = new_path
            logger.debug(
                f"移動計画: {file_path.relative_to(src_root)} → {new_path.relative_to(src_root)}",
                depth=depth,
                folder_name=folder_name
            )
    
    return move_plan

def _execute_reorganization(src_root: Path, move_plan: Dict[Path, Path],
                          config: ReorganizerConfig, logger,
                          error_collector: ErrorCollector, 
                          start_time: float) -> CheckResult:
    """ファイル移動を実行"""
    # Phase 3: インポート更新
    phase_start = time.time()
    logger.log_phase_start("Phase 3", "インポート文の更新")
    
    updater = ImportUpdaterV3(src_root)
    updater.set_move_plan(move_plan)
    
    try:
        import_changes = updater.update_all_files(dry_run=False)
        logger.info(f"インポート更新完了: {len(import_changes)}ファイル")
        logger.log_phase_end("Phase 3", True, time.time() - phase_start)
    except Exception as e:
        logger.error(f"インポート更新エラー: {str(e)}")
        error_collector.add_error(ImportUpdateError(Path("unknown"), str(e)))
        return _create_error_result(error_collector, start_time)
    
    # Phase 4: ファイル移動
    phase_start = time.time()
    logger.log_phase_start("Phase 4", "ファイル移動の実行")
    
    mover = FileMover(src_root, use_git=config.use_git_backup)
    
    # バックアップ作成
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir_name = config.backup_dir_name.format(timestamp=timestamp)
    backup_path = mover.create_backup(move_plan)
    
    if backup_path:
        logger.info(f"バックアップ作成: {backup_path}")
    
    # ファイル移動実行
    success_count, move_errors = mover.execute_moves(
        move_plan, 
        create_init_files=config.create_init_files
    )
    
    for error_msg in move_errors:
        error_collector.add_error(FileMoveError(Path("unknown"), Path("unknown"), error_msg))
    
    logger.log_phase_end("Phase 4", len(move_errors) == 0, time.time() - phase_start)
    
    # Phase 5: 検証
    if config.validate_syntax or config.validate_imports:
        phase_start = time.time()
        logger.log_phase_start("Phase 5", "移動後の検証")
        
        validator = SyntaxValidator(src_root)
        
        if config.validate_syntax:
            syntax_errors = validator.validate_all_files(list(move_plan.values()))
            if syntax_errors:
                failures = [
                    {"file": str(f), "error": e} 
                    for f, e in syntax_errors.items()
                ]
                error_collector.add_error(ValidationError("構文", failures))
        
        if config.validate_imports:
            import_errors = {}
            for new_path in move_plan.values():
                if new_path.exists():
                    unresolved = validator.validate_imports(new_path)
                    if unresolved:
                        import_errors[new_path] = unresolved
            
            if import_errors:
                failures = [
                    {"file": str(f), "imports": i}
                    for f, i in import_errors.items()
                ]
                error_collector.add_error(ValidationError("インポート", failures))
        
        logger.log_phase_end("Phase 5", 
                           not (syntax_errors or import_errors), 
                           time.time() - phase_start)
    
    # レポート保存
    report_path = mover.save_move_report(move_plan, success_count, move_errors)
    
    # テスト実行（オプション）
    if config.run_tests_after and not error_collector.has_critical_errors():
        phase_start = time.time()
        logger.log_phase_start("Phase 6", "テストの実行")
        
        import subprocess
        result = subprocess.run(
            config.test_command.split(),
            cwd=src_root.parent,
            capture_output=True,
            text=True
        )
        
        test_success = result.returncode == 0
        if not test_success:
            error_collector.add_warning(
                "test_failure",
                f"テストが失敗しました: {config.test_command}",
                {"stdout": result.stdout[-500:], "stderr": result.stderr[-500:]}
            )
        
        logger.log_phase_end("Phase 6", test_success, time.time() - phase_start)
    
    # 最終結果
    total_time = time.time() - start_time
    
    if error_collector.has_critical_errors():
        return _create_error_result(error_collector, start_time)
    
    return CheckResult(
        failure_locations=[],
        fix_policy=f"ファイル移動完了: {success_count}/{len(move_plan)}成功 (実行時間: {total_time:.2f}秒)",
        fix_example_code=f"詳細レポート: {report_path}\n{error_collector.format_report()}"
    )

def _create_error_result(error_collector: ErrorCollector, 
                        start_time: float) -> CheckResult:
    """エラー結果を作成"""
    summary = error_collector.get_summary()
    total_time = time.time() - start_time
    
    failures = []
    for error in error_collector.errors[:10]:  # 最初の10個
        failures.append(FailureLocation(
            file_path=error.details.get("file_path", "unknown"),
            line_number=error.details.get("line_number", 0)
        ))
    
    return CheckResult(
        failure_locations=failures,
        fix_policy=f"エラーが発生しました: {summary['total_errors']}個のエラー, {summary['total_warnings']}個の警告 (実行時間: {total_time:.2f}秒)",
        fix_example_code=error_collector.format_report()
    )

def _generate_html_viewer(json_path: Path, output_path: Path) -> None:
    """JSONデータからHTMLビューアを生成"""
    # テンプレートを読み込み
    template_path = Path(__file__).parent / "graph_viewer_template.html"
    template_content = template_path.read_text(encoding='utf-8')
    
    # JSONデータを読み込み
    with open(json_path, 'r', encoding='utf-8') as f:
        graph_data = json.load(f)
    
    # プレースホルダーを置換
    html_content = template_content.replace(
        'GRAPH_DATA_PLACEHOLDER',
        json.dumps(graph_data, ensure_ascii=False, indent=2)
    )
    
    # HTMLファイルを保存
    output_path.write_text(html_content, encoding='utf-8')

if __name__ == "__main__":
    # コマンドライン引数処理（簡易版）
    import argparse
    
    parser = argparse.ArgumentParser(description="依存関係ベースフォルダ構造整理ツール")
    parser.add_argument("--config", type=Path, help="設定ファイルパス")
    parser.add_argument("--execute", action="store_true", help="実行モード")
    parser.add_argument("--verbose", action="store_true", help="詳細ログ")
    
    args = parser.parse_args()
    
    # 設定作成
    config = None
    if args.config:
        config = ReorganizerConfig.from_file(args.config)
    else:
        config = create_default_config()
    
    if args.execute:
        config.execute_mode = True
        config.dry_run = False
    
    if args.verbose:
        config.verbose = True
        config.log_level = "DEBUG"
    
    # 実行
    result = main(config)
    print(f"\n結果: {result.fix_policy}")
    if result.fix_example_code:
        print(f"\n詳細:\n{result.fix_example_code}")