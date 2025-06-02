"""
出力表示制御の純粋関数実装
出力判定ロジックと実際の出力を分離
"""
from dataclasses import dataclass
from typing import Any, List, Optional, Dict, Tuple, Union, Callable
from enum import Enum


class OutputType(Enum):
    """出力タイプの列挙"""
    STDOUT = "stdout"
    STDERR = "stderr"
    COMBINED = "combined"
    NONE = "none"


@dataclass(frozen=True)
class OutputContent:
    """出力内容の不変データクラス"""
    stdout: str = ""
    stderr: str = ""
    
    def has_stdout(self) -> bool:
        """標準出力があるかどうか"""
        return bool(self.stdout.strip())
    
    def has_stderr(self) -> bool:
        """標準エラー出力があるかどうか"""
        return bool(self.stderr.strip())
    
    def has_any_output(self) -> bool:
        """何らかの出力があるかどうか"""
        return self.has_stdout() or self.has_stderr()
    
    def get_combined(self) -> str:
        """結合された出力を取得"""
        parts = []
        if self.stdout:
            parts.append(self.stdout)
        if self.stderr:
            parts.append(self.stderr)
        return "".join(parts)


@dataclass(frozen=True)
class RequestInfo:
    """リクエスト情報の不変データクラス"""
    show_output: bool = False
    request_type: str = "unknown"
    allow_failure: bool = False
    name: Optional[str] = None
    
    @classmethod
    def from_request(cls, request: Any) -> 'RequestInfo':
        """リクエストオブジェクトからRequestInfoを作成"""
        return cls(
            show_output=getattr(request, 'show_output', False),
            request_type=getattr(request, 'request_type', 'unknown'),
            allow_failure=getattr(request, 'allow_failure', False),
            name=getattr(request, 'name', None)
        )


@dataclass(frozen=True)
class OutputDecision:
    """出力判定結果の不変データクラス"""
    should_show_stdout: bool
    should_show_stderr: bool
    output_type: OutputType
    reason: str
    filter_applied: bool = False


@dataclass(frozen=True)
class OutputAction:
    """出力アクションの不変データクラス"""
    content: str
    output_type: OutputType
    metadata: Dict[str, Any]
    
    def __post_init__(self):
        if self.metadata is None:
            object.__setattr__(self, 'metadata', {})


@dataclass(frozen=True)
class OutputProcessingResult:
    """出力処理結果の不変データクラス"""
    actions: List[OutputAction]
    decisions: List[OutputDecision]
    summary: Dict[str, Any]
    
    def __post_init__(self):
        if self.actions is None:
            object.__setattr__(self, 'actions', [])
        if self.decisions is None:
            object.__setattr__(self, 'decisions', [])
        if self.summary is None:
            object.__setattr__(self, 'summary', {})


def should_show_output_pure(request_info: RequestInfo, output_content: OutputContent) -> OutputDecision:
    """
    出力を表示すべきかどうかを判定する純粋関数
    
    Args:
        request_info: リクエスト情報
        output_content: 出力内容
        
    Returns:
        OutputDecision: 出力判定結果
    """
    # 基本的な表示判定
    if not request_info.show_output:
        return OutputDecision(
            should_show_stdout=False,
            should_show_stderr=False,
            output_type=OutputType.NONE,
            reason="show_output is disabled"
        )
    
    # 出力内容がない場合
    if not output_content.has_any_output():
        return OutputDecision(
            should_show_stdout=False,
            should_show_stderr=False,
            output_type=OutputType.NONE,
            reason="no output content"
        )
    
    # 標準出力と標準エラー出力の判定
    show_stdout = output_content.has_stdout()
    show_stderr = output_content.has_stderr()
    
    if show_stdout and show_stderr:
        output_type = OutputType.COMBINED
        reason = "both stdout and stderr available"
    elif show_stdout:
        output_type = OutputType.STDOUT
        reason = "stdout available"
    elif show_stderr:
        output_type = OutputType.STDERR
        reason = "stderr available"
    else:
        output_type = OutputType.NONE
        reason = "no meaningful output"
    
    return OutputDecision(
        should_show_stdout=show_stdout,
        should_show_stderr=show_stderr,
        output_type=output_type,
        reason=reason
    )


def create_output_actions_pure(
    output_content: OutputContent,
    decision: OutputDecision
) -> List[OutputAction]:
    """
    出力判定結果から出力アクションを作成する純粋関数
    
    Args:
        output_content: 出力内容
        decision: 出力判定結果
        
    Returns:
        出力アクションのリスト
    """
    actions = []
    
    if decision.should_show_stdout and output_content.has_stdout():
        actions.append(OutputAction(
            content=output_content.stdout,
            output_type=OutputType.STDOUT,
            metadata={"source": "stdout", "length": len(output_content.stdout)}
        ))
    
    if decision.should_show_stderr and output_content.has_stderr():
        actions.append(OutputAction(
            content=output_content.stderr,
            output_type=OutputType.STDERR,
            metadata={"source": "stderr", "length": len(output_content.stderr)}
        ))
    
    return actions


def filter_output_content_pure(
    content: str,
    filters: List[str]
) -> Tuple[str, bool]:
    """
    出力内容をフィルタリングする純粋関数
    
    Args:
        content: フィルタリング対象の内容
        filters: フィルタパターンのリスト
        
    Returns:
        Tuple[str, bool]: (フィルタ後の内容, フィルタが適用されたかどうか)
    """
    if not filters or not content:
        return content, False
    
    filtered_content = content
    filter_applied = False
    
    for filter_pattern in filters:
        if filter_pattern in filtered_content:
            filtered_content = filtered_content.replace(filter_pattern, "")
            filter_applied = True
    
    return filtered_content, filter_applied


def process_multiple_outputs_pure(
    requests_and_results: List[Tuple[RequestInfo, OutputContent]],
    global_filters: Optional[List[str]] = None
) -> OutputProcessingResult:
    """
    複数のリクエスト/結果ペアの出力を処理する純粋関数
    
    Args:
        requests_and_results: (リクエスト情報, 出力内容)のタプルのリスト
        global_filters: グローバルフィルタ
        
    Returns:
        OutputProcessingResult: 処理結果
    """
    all_actions = []
    all_decisions = []
    
    for request_info, output_content in requests_and_results:
        # フィルタリング適用
        if global_filters:
            filtered_stdout, stdout_filtered = filter_output_content_pure(
                output_content.stdout, global_filters
            )
            filtered_stderr, stderr_filtered = filter_output_content_pure(
                output_content.stderr, global_filters
            )
            
            filtered_content = OutputContent(
                stdout=filtered_stdout,
                stderr=filtered_stderr
            )
        else:
            filtered_content = output_content
            stdout_filtered = stderr_filtered = False
        
        # 出力判定
        decision = should_show_output_pure(request_info, filtered_content)
        decision = OutputDecision(
            should_show_stdout=decision.should_show_stdout,
            should_show_stderr=decision.should_show_stderr,
            output_type=decision.output_type,
            reason=decision.reason,
            filter_applied=stdout_filtered or stderr_filtered
        )
        
        # アクション作成
        actions = create_output_actions_pure(filtered_content, decision)
        
        all_decisions.append(decision)
        all_actions.extend(actions)
    
    # サマリー作成
    summary = {
        "total_requests": len(requests_and_results),
        "requests_with_output": sum(1 for _, content in requests_and_results if content.has_any_output()),
        "total_actions": len(all_actions),
        "stdout_actions": len([a for a in all_actions if a.output_type == OutputType.STDOUT]),
        "stderr_actions": len([a for a in all_actions if a.output_type == OutputType.STDERR]),
        "filtered_outputs": sum(1 for d in all_decisions if d.filter_applied)
    }
    
    return OutputProcessingResult(
        actions=all_actions,
        decisions=all_decisions,
        summary=summary
    )


def analyze_output_patterns_pure(
    output_contents: List[OutputContent]
) -> Dict[str, Any]:
    """
    出力パターンを分析する純粋関数
    
    Args:
        output_contents: 出力内容のリスト
        
    Returns:
        分析結果の辞書
    """
    if not output_contents:
        return {
            "total_outputs": 0,
            "has_stdout": 0,
            "has_stderr": 0,
            "avg_stdout_length": 0,
            "avg_stderr_length": 0,
            "common_patterns": []
        }
    
    stdout_counts = sum(1 for content in output_contents if content.has_stdout())
    stderr_counts = sum(1 for content in output_contents if content.has_stderr())
    
    stdout_lengths = [len(content.stdout) for content in output_contents if content.has_stdout()]
    stderr_lengths = [len(content.stderr) for content in output_contents if content.has_stderr()]
    
    avg_stdout_length = sum(stdout_lengths) / len(stdout_lengths) if stdout_lengths else 0
    avg_stderr_length = sum(stderr_lengths) / len(stderr_lengths) if stderr_lengths else 0
    
    # 共通パターンの検出（簡易版）
    all_stdout_lines = []
    for content in output_contents:
        if content.has_stdout():
            all_stdout_lines.extend(content.stdout.splitlines())
    
    # 頻出行の検出
    line_counts = {}
    for line in all_stdout_lines:
        line = line.strip()
        if line:
            line_counts[line] = line_counts.get(line, 0) + 1
    
    common_patterns = [
        line for line, count in line_counts.items() 
        if count > 1 and len(line) > 5  # 短すぎる行は除外
    ][:5]  # 上位5つ
    
    return {
        "total_outputs": len(output_contents),
        "has_stdout": stdout_counts,
        "has_stderr": stderr_counts,
        "avg_stdout_length": avg_stdout_length,
        "avg_stderr_length": avg_stderr_length,
        "common_patterns": common_patterns,
        "stdout_stderr_ratio": stdout_counts / stderr_counts if stderr_counts > 0 else float('inf')
    }


def create_output_summary_pure(
    actions: List[OutputAction],
    include_content_sample: bool = False
) -> Dict[str, Any]:
    """
    出力アクションのサマリーを作成する純粋関数
    
    Args:
        actions: 出力アクションのリスト
        include_content_sample: 内容サンプルを含めるかどうか
        
    Returns:
        サマリー辞書
    """
    if not actions:
        return {
            "total_actions": 0,
            "by_type": {},
            "total_content_length": 0,
            "content_sample": None if include_content_sample else "not_included"
        }
    
    # タイプ別集計
    by_type = {}
    total_length = 0
    
    for action in actions:
        output_type = action.output_type.value
        if output_type not in by_type:
            by_type[output_type] = {
                "count": 0,
                "total_length": 0,
                "avg_length": 0
            }
        
        by_type[output_type]["count"] += 1
        content_length = len(action.content)
        by_type[output_type]["total_length"] += content_length
        total_length += content_length
    
    # 平均長の計算
    for type_info in by_type.values():
        type_info["avg_length"] = type_info["total_length"] / type_info["count"]
    
    # 内容サンプル
    content_sample = None
    if include_content_sample and actions:
        # 最初のアクションから最大100文字のサンプルを取得
        sample_content = actions[0].content[:100]
        if len(actions[0].content) > 100:
            sample_content += "..."
        content_sample = sample_content
    
    return {
        "total_actions": len(actions),
        "by_type": by_type,
        "total_content_length": total_length,
        "avg_content_length": total_length / len(actions),
        "content_sample": content_sample if include_content_sample else "not_included"
    }


def optimize_output_display_pure(
    actions: List[OutputAction],
    max_length: Optional[int] = None,
    deduplicate: bool = False
) -> List[OutputAction]:
    """
    出力表示を最適化する純粋関数
    
    Args:
        actions: 出力アクション
        max_length: 最大長制限
        deduplicate: 重複除去するかどうか
        
    Returns:
        最適化された出力アクション
    """
    if not actions:
        return []
    
    optimized_actions = list(actions)
    
    # 重複除去
    if deduplicate:
        seen_content = set()
        deduplicated_actions = []
        
        for action in optimized_actions:
            content_hash = hash(action.content)
            if content_hash not in seen_content:
                seen_content.add(content_hash)
                deduplicated_actions.append(action)
        
        optimized_actions = deduplicated_actions
    
    # 長さ制限
    if max_length is not None:
        length_limited_actions = []
        
        for action in optimized_actions:
            if len(action.content) <= max_length:
                length_limited_actions.append(action)
            else:
                # 内容を切り詰める
                truncated_content = action.content[:max_length] + "..."
                truncated_action = OutputAction(
                    content=truncated_content,
                    output_type=action.output_type,
                    metadata={
                        **action.metadata,
                        "truncated": True,
                        "original_length": len(action.content)
                    }
                )
                length_limited_actions.append(truncated_action)
        
        optimized_actions = length_limited_actions
    
    return optimized_actions


def validate_output_configuration_pure(
    config: Dict[str, Any]
) -> Tuple[bool, List[str]]:
    """
    出力設定の妥当性を検証する純粋関数
    
    Args:
        config: 出力設定辞書
        
    Returns:
        Tuple[bool, List[str]]: (有効かどうか, エラーメッセージ)
    """
    errors = []
    
    # 必要なキーの確認
    required_keys = ["show_output"]
    for key in required_keys:
        if key not in config:
            errors.append(f"Required key '{key}' is missing")
    
    # show_outputの型確認
    if "show_output" in config and not isinstance(config["show_output"], bool):
        errors.append("show_output must be a boolean")
    
    # フィルタの確認
    if "filters" in config:
        if not isinstance(config["filters"], list):
            errors.append("filters must be a list")
        elif not all(isinstance(f, str) for f in config["filters"]):
            errors.append("all filter items must be strings")
    
    # 最大長の確認
    if "max_length" in config:
        if not isinstance(config["max_length"], int) or config["max_length"] < 0:
            errors.append("max_length must be a non-negative integer")
    
    return len(errors) == 0, errors