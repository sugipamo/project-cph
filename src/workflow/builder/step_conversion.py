"""ステップからリクエストへの変換機能 - GraphBasedWorkflowBuilderから分離"""
from typing import Any, Optional, Set, Tuple, Dict, List
from pathlib import Path
from dataclasses import dataclass


@dataclass(frozen=True)
class StepConversionResult:
    """ステップ変換結果（不変データ構造）"""
    request: Optional[Any]
    resource_info: Tuple[Set[str], Set[str], Set[str], Set[str]]  # creates_files, creates_dirs, reads_files, requires_dirs
    metadata: Dict[str, Any]
    errors: List[str]
    warnings: List[str]
    
    @property
    def is_success(self) -> bool:
        """変換成功判定（純粋関数）"""
        return self.request is not None and not self.errors


def convert_step_to_request(step: Any, context: Optional[Any] = None) -> StepConversionResult:
    """StepからRequestを生成（純粋関数版）
    
    Args:
        step: 変換するステップ
        context: ステップコンテキスト
        
    Returns:
        変換結果
    """
    try:
        from src.application.factories.unified_request_factory import create_request
        
        # 統一ファクトリを使用してリクエストを生成
        request = create_request(step, context=context)
        
        if request is None:
            return StepConversionResult(
                request=None,
                resource_info=(set(), set(), set(), set()),
                metadata={},
                errors=[f"Failed to create request for step type: {getattr(step, 'type', 'unknown')}"],
                warnings=[]
            )
        
        # リソース情報を抽出
        resource_info = extract_step_resource_info(step)
        
        # メタデータを作成
        metadata = extract_step_metadata(step)
        
        return StepConversionResult(
            request=request,
            resource_info=resource_info,
            metadata=metadata,
            errors=[],
            warnings=[]
        )
        
    except Exception as e:
        return StepConversionResult(
            request=None,
            resource_info=(set(), set(), set(), set()),
            metadata={},
            errors=[f"Step conversion failed: {str(e)}"],
            warnings=[]
        )


def extract_step_resource_info(step: Any) -> Tuple[Set[str], Set[str], Set[str], Set[str]]:
    """ステップからリソース情報を抽出（純粋関数）
    
    Args:
        step: ステップオブジェクト
        
    Returns:
        (creates_files, creates_dirs, reads_files, requires_dirs)のタプル
    """
    try:
        from src.workflow.builder.graph_builder_utils import extract_node_resource_info
        return extract_node_resource_info(step)
    except ImportError:
        # フォールバック実装
        return _extract_resource_info_fallback(step)


def _extract_resource_info_fallback(step: Any) -> Tuple[Set[str], Set[str], Set[str], Set[str]]:
    """リソース情報抽出のフォールバック実装（純粋関数）"""
    creates_files = set()
    creates_dirs = set()
    reads_files = set()
    requires_dirs = set()
    
    # ステップタイプ別の簡易的なリソース推定
    if hasattr(step, 'type') and hasattr(step, 'cmd'):
        step_type = getattr(step.type, 'value', str(step.type))
        cmd = step.cmd or ""
        
        # ファイル操作の検出
        if 'touch' in cmd or 'echo' in cmd and '>' in cmd:
            # ファイル作成を検出
            file_paths = _extract_file_paths_from_command(cmd, create_mode=True)
            creates_files.update(file_paths)
            
            # 親ディレクトリを requires_dirs に追加
            for file_path in file_paths:
                parent_dir = str(Path(file_path).parent)
                if parent_dir != '.':
                    requires_dirs.add(parent_dir)
        
        if 'mkdir' in cmd:
            # ディレクトリ作成を検出
            dir_paths = _extract_dir_paths_from_command(cmd)
            creates_dirs.update(dir_paths)
        
        if 'cat' in cmd or 'grep' in cmd or '<' in cmd:
            # ファイル読み取りを検出
            file_paths = _extract_file_paths_from_command(cmd, create_mode=False)
            reads_files.update(file_paths)
            
            # 親ディレクトリを requires_dirs に追加
            for file_path in file_paths:
                parent_dir = str(Path(file_path).parent)
                if parent_dir != '.':
                    requires_dirs.add(parent_dir)
    
    return creates_files, creates_dirs, reads_files, requires_dirs


def _extract_file_paths_from_command(cmd: str, create_mode: bool = False) -> Set[str]:
    """コマンドからファイルパスを抽出（純粋関数）"""
    import re
    
    file_paths = set()
    
    if create_mode:
        # ファイル作成パターン
        patterns = [
            r'touch\s+([^\s]+)',
            r'echo.*>\s*([^\s]+)',
            r'cat.*>\s*([^\s]+)',
        ]
    else:
        # ファイル読み取りパターン
        patterns = [
            r'cat\s+([^\s]+)',
            r'grep.*\s+([^\s]+)',
            r'<\s*([^\s]+)',
        ]
    
    for pattern in patterns:
        matches = re.findall(pattern, cmd)
        for match in matches:
            # 基本的なパス正規化
            path = match.strip()
            if path and not path.startswith('-'):  # オプションでない場合
                file_paths.add(path)
    
    return file_paths


def _extract_dir_paths_from_command(cmd: str) -> Set[str]:
    """コマンドからディレクトリパスを抽出（純粋関数）"""
    import re
    
    dir_paths = set()
    
    # mkdir パターン
    patterns = [
        r'mkdir\s+(?:-p\s+)?([^\s]+)',
        r'mkdir\s+([^\s]+)',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, cmd)
        for match in matches:
            # 基本的なパス正規化
            path = match.strip()
            if path and not path.startswith('-'):  # オプションでない場合
                dir_paths.add(path)
    
    return dir_paths


def extract_step_metadata(step: Any) -> Dict[str, Any]:
    """ステップからメタデータを抽出（純粋関数）
    
    Args:
        step: ステップオブジェクト
        
    Returns:
        メタデータ辞書
    """
    metadata = {}
    
    # 基本情報
    if hasattr(step, 'type'):
        metadata['step_type'] = getattr(step.type, 'value', str(step.type))
    
    if hasattr(step, 'cmd'):
        metadata['step_cmd'] = step.cmd
    
    if hasattr(step, 'allow_failure'):
        metadata['allow_failure'] = step.allow_failure
    
    if hasattr(step, 'show_output'):
        metadata['show_output'] = step.show_output
    
    # 追加のステップ属性
    for attr in ['timeout', 'working_dir', 'env_vars', 'description']:
        if hasattr(step, attr):
            value = getattr(step, attr)
            if value is not None:
                metadata[attr] = value
    
    return metadata


def validate_step_conversion(step: Any, request: Any) -> List[str]:
    """ステップ変換の妥当性を検証（純粋関数）
    
    Args:
        step: 元のステップ
        request: 変換されたリクエスト
        
    Returns:
        エラーメッセージリスト
    """
    errors = []
    
    if request is None:
        errors.append("Request is None")
        return errors
    
    # リクエストタイプの妥当性チェック
    if not hasattr(request, 'execute'):
        errors.append("Request doesn't have execute method")
    
    # ステップとリクエストの一貫性チェック
    if hasattr(step, 'allow_failure') and hasattr(request, 'allow_failure'):
        if step.allow_failure != request.allow_failure:
            errors.append("allow_failure mismatch between step and request")
    
    # コマンド系ステップの特別な検証
    if hasattr(step, 'cmd') and step.cmd:
        if hasattr(request, 'cmd'):
            if request.cmd != step.cmd:
                errors.append("Command mismatch between step and request")
        elif hasattr(request, 'command'):
            if request.command != step.cmd:
                errors.append("Command mismatch between step and request")
        else:
            errors.append("Step has command but request doesn't")
    
    return errors


def batch_convert_steps(steps: List[Any], context: Optional[Any] = None) -> List[StepConversionResult]:
    """複数ステップを一括変換（純粋関数）
    
    Args:
        steps: ステップリスト
        context: ステップコンテキスト
        
    Returns:
        変換結果リスト
    """
    results = []
    
    for step in steps:
        result = convert_step_to_request(step, context)
        results.append(result)
    
    return results


def analyze_conversion_results(results: List[StepConversionResult]) -> Dict[str, Any]:
    """変換結果を分析（純粋関数）
    
    Args:
        results: 変換結果リスト
        
    Returns:
        分析結果辞書
    """
    total_steps = len(results)
    successful_conversions = sum(1 for r in results if r.is_success)
    failed_conversions = total_steps - successful_conversions
    
    all_errors = []
    all_warnings = []
    
    for result in results:
        all_errors.extend(result.errors)
        all_warnings.extend(result.warnings)
    
    # リクエストタイプ別統計
    request_types = {}
    for result in results:
        if result.request is not None:
            request_type = type(result.request).__name__
            request_types[request_type] = request_types.get(request_type, 0) + 1
    
    return {
        'total_steps': total_steps,
        'successful_conversions': successful_conversions,
        'failed_conversions': failed_conversions,
        'success_rate': (successful_conversions / total_steps * 100) if total_steps > 0 else 0,
        'total_errors': len(all_errors),
        'total_warnings': len(all_warnings),
        'request_type_distribution': request_types,
        'errors': all_errors,
        'warnings': all_warnings
    }


def create_conversion_summary(results: List[StepConversionResult]) -> str:
    """変換結果のサマリー文字列を作成（純粋関数）
    
    Args:
        results: 変換結果リスト
        
    Returns:
        サマリー文字列
    """
    analysis = analyze_conversion_results(results)
    
    lines = [
        "Step Conversion Summary:",
        f"  Total steps: {analysis['total_steps']}",
        f"  Successful conversions: {analysis['successful_conversions']}",
        f"  Failed conversions: {analysis['failed_conversions']}",
        f"  Success rate: {analysis['success_rate']:.1f}%",
        ""
    ]
    
    if analysis['request_type_distribution']:
        lines.append("Request type distribution:")
        for request_type, count in analysis['request_type_distribution'].items():
            lines.append(f"  {request_type}: {count}")
        lines.append("")
    
    if analysis['errors']:
        lines.append("Errors:")
        for error in analysis['errors'][:5]:  # 最初の5個のエラーのみ表示
            lines.append(f"  - {error}")
        if len(analysis['errors']) > 5:
            lines.append(f"  ... and {len(analysis['errors']) - 5} more errors")
        lines.append("")
    
    if analysis['warnings']:
        lines.append("Warnings:")
        for warning in analysis['warnings'][:3]:  # 最初の3個の警告のみ表示
            lines.append(f"  - {warning}")
        if len(analysis['warnings']) > 3:
            lines.append(f"  ... and {len(analysis['warnings']) - 3} more warnings")
    
    return "\n".join(lines)