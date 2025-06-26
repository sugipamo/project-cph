"""
結果出力機能
CheckResultを指定ディレクトリにファイル出力
"""

import os
import sys
from pathlib import Path
from typing import List

sys.path.append(str(Path(__file__).parent.parent))
from models.check_result import CheckResult


class ResultWriter:
    """CheckResult出力管理クラス"""
    
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self._ensure_output_dir()
    
    def _ensure_output_dir(self):
        """出力ディレクトリが存在しない場合は作成"""
        if not self.output_dir.exists():
            self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def write_result(self, result: CheckResult) -> Path:
        """
        CheckResultを{title}.txtファイルに出力
        """
        # ファイル名をサニタイズ
        safe_title = self._sanitize_filename(result.title)
        output_file = self.output_dir / f"{safe_title}.txt"
        
        # 結果を整形
        content = self._format_result(result)
        
        # ファイルに書き込み
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return output_file
    
    def write_results(self, results: List[CheckResult]) -> List[Path]:
        """
        複数のCheckResultを一括出力
        """
        output_files = []
        for result in results:
            output_file = self.write_result(result)
            output_files.append(output_file)
        
        return output_files
    
    def _sanitize_filename(self, filename: str) -> str:
        """
        ファイル名をサニタイズ（不正な文字を除去）
        """
        # 不正な文字を除去
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        
        # 連続するアンダースコアを単一に
        while '__' in filename:
            filename = filename.replace('__', '_')
        
        # 前後のアンダースコアを削除
        filename = filename.strip('_')
        
        # 空の場合はデフォルト名
        if not filename:
            filename = "unknown_result"
        
        return filename
    
    def _format_result(self, result: CheckResult) -> str:
        """
        CheckResultを読みやすい形式に整形
        """
        lines = []
        
        # タイトル
        lines.append(f"=== {result.title} ===")
        lines.append("")
        
        # 失敗箇所
        if result.failure_locations:
            lines.append(f"失敗箇所: {len(result.failure_locations)}件")
            lines.append("-" * 40)
            
            for i, location in enumerate(result.failure_locations, 1):
                lines.append(f"{i}. {location.file_path}:{location.line_number}")
            
            lines.append("")
        else:
            lines.append("失敗箇所: なし")
            lines.append("")
        
        # 修正方針
        if result.fix_policy:
            lines.append("修正方針:")
            lines.append("-" * 20)
            lines.append(result.fix_policy)
            lines.append("")
        
        # 修正例
        if result.fix_example_code:
            lines.append("修正例:")
            lines.append("-" * 20)
            lines.append(result.fix_example_code)
            lines.append("")
        
        # 実行時刻
        from datetime import datetime
        lines.append(f"実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return "\n".join(lines)
    
    def create_summary_report(self, results: List[CheckResult]) -> Path:
        """
        全結果のサマリーレポートを作成
        """
        summary_file = self.output_dir / "summary.txt"
        
        lines = []
        lines.append("=== src_check 実行結果サマリー ===")
        lines.append("")
        
        # 統計情報
        total_modules = len(results)
        total_failures = sum(len(r.failure_locations) for r in results)
        failed_modules = sum(1 for r in results if r.failure_locations)
        
        lines.append(f"実行モジュール数: {total_modules}")
        lines.append(f"失敗モジュール数: {failed_modules}")
        lines.append(f"総失敗件数: {total_failures}")
        lines.append("")
        
        # 各モジュールの結果
        lines.append("モジュール別結果:")
        lines.append("-" * 50)
        
        for result in results:
            status = "OK" if not result.failure_locations else f"NG({len(result.failure_locations)}件)"
            lines.append(f"{result.title}: {status}")
        
        lines.append("")
        
        # 実行時刻
        from datetime import datetime
        lines.append(f"実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines))
        
        return summary_file