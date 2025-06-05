"""
OutputManager特化フォーマット処理

OutputManager固有のフォーマット機能を提供
基底レイヤーを継承して出力特化機能を追加
"""
from dataclasses import dataclass
from typing import Optional, Tuple, Dict, Any, Union, List

from .core import FormattingCore, FormatOperationResult


@dataclass(frozen=True)
class OutputFormatData:
    """出力フォーマット用の不変データクラス"""
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    return_code: Optional[int] = None
    execution_time: Optional[float] = None
    memory_usage: Optional[str] = None
    
    # 出力制御オプション
    show_output: bool = True
    show_errors: bool = True
    show_timing: bool = False
    max_output_length: int = 10000


class OutputManagerFormatter(FormattingCore):
    """OutputManager特化のフォーマット処理クラス"""
    
    @staticmethod
    def extract_output_data(result,
                          strict: bool = False) -> Union[OutputFormatData, FormatOperationResult]:
        """結果オブジェクトから出力データを抽出
        
        Args:
            result: 実行結果オブジェクト
            strict: Trueの場合、詳細な結果型を返す
            
        Returns:
            strict=Falseの場合: OutputFormatData
            strict=Trueの場合: FormatOperationResult
        """
        try:
            warnings = []
            
            # 標準出力の抽出
            stdout = getattr(result, 'stdout', None)
            if stdout is not None and not isinstance(stdout, str):
                stdout = str(stdout)
                warnings.append("stdout was converted to string")
            
            # 標準エラーの抽出
            stderr = getattr(result, 'stderr', None)
            if stderr is not None and not isinstance(stderr, str):
                stderr = str(stderr)
                warnings.append("stderr was converted to string")
            
            # リターンコードの抽出
            return_code = getattr(result, 'return_code', None)
            if return_code is None:
                return_code = getattr(result, 'returncode', None)
            if return_code is not None and not isinstance(return_code, int):
                try:
                    return_code = int(return_code)
                except (ValueError, TypeError):
                    return_code = None
                    warnings.append("return_code could not be converted to int")
            
            # 実行時間の抽出
            execution_time = getattr(result, 'execution_time', None)
            if execution_time is None:
                execution_time = getattr(result, 'elapsed_time', None)
            if execution_time is not None and not isinstance(execution_time, (int, float)):
                try:
                    execution_time = float(execution_time)
                except (ValueError, TypeError):
                    execution_time = None
                    warnings.append("execution_time could not be converted to float")
            
            # メモリ使用量の抽出
            memory_usage = getattr(result, 'memory_usage', None)
            if memory_usage is not None and not isinstance(memory_usage, str):
                memory_usage = str(memory_usage)
                warnings.append("memory_usage was converted to string")
            
            # 出力制御オプションの抽出
            show_output = getattr(result, 'show_output', True)
            if not isinstance(show_output, bool):
                show_output = bool(show_output)
                warnings.append("show_output was converted to bool")
            
            output_data = OutputFormatData(
                stdout=stdout,
                stderr=stderr,
                return_code=return_code,
                execution_time=execution_time,
                memory_usage=memory_usage,
                show_output=show_output
            )
            
            if strict:
                return FormatOperationResult(
                    success=True,
                    result=None,
                    missing_keys=[],
                    errors=[],
                    warnings=warnings,
                    metadata={
                        "result_type": type(result).__name__,
                        "has_stdout": stdout is not None,
                        "has_stderr": stderr is not None,
                        "has_return_code": return_code is not None
                    }
                )
            else:
                return output_data
                
        except Exception as e:
            error_msg = f"Failed to extract output data: {e}"
            if strict:
                return FormatOperationResult(
                    success=False,
                    result=None,
                    missing_keys=[],
                    errors=[error_msg],
                    warnings=[],
                    metadata={"result": str(result)}
                )
            else:
                raise ValueError(error_msg)
    
    @staticmethod
    def should_show_output(request,
                          strict: bool = False) -> Union[bool, FormatOperationResult]:
        """リクエストから出力表示フラグを判定
        
        Args:
            request: リクエストオブジェクト
            strict: Trueの場合、詳細な結果型を返す
            
        Returns:
            strict=Falseの場合: bool
            strict=Trueの場合: FormatOperationResult
        """
        try:
            show_output = hasattr(request, 'show_output') and bool(request.show_output)
            
            if strict:
                return FormatOperationResult(
                    success=True,
                    result=str(show_output),
                    missing_keys=[],
                    errors=[],
                    warnings=[],
                    metadata={
                        "request_type": type(request).__name__,
                        "has_show_output_attr": hasattr(request, 'show_output'),
                        "show_output_value": getattr(request, 'show_output', None)
                    }
                )
            else:
                return show_output
                
        except Exception as e:
            error_msg = f"Failed to determine output visibility: {e}"
            if strict:
                return FormatOperationResult(
                    success=False,
                    result=None,
                    missing_keys=[],
                    errors=[error_msg],
                    warnings=[],
                    metadata={"request": str(request)}
                )
            else:
                return False
    
    @staticmethod
    def format_output_content(output_data: OutputFormatData,
                            template: Optional[str] = None,
                            strict: bool = False) -> Union[str, FormatOperationResult]:
        """出力データから表示用テキストを生成
        
        Args:
            output_data: 出力データ
            template: カスタムテンプレート（Noneの場合はデフォルト）
            strict: Trueの場合、詳細な結果型を返す
            
        Returns:
            strict=Falseの場合: フォーマット済み出力文字列
            strict=Trueの場合: FormatOperationResult
        """
        try:
            if template is None:
                # デフォルトテンプレート
                if output_data.show_timing and output_data.execution_time is not None:
                    template = "{stdout}{stderr}実行時間: {execution_time:.3f}秒"
                else:
                    template = "{stdout}{stderr}"
            
            # フォーマット用辞書を作成
            format_dict = {}
            
            # 標準出力の処理
            if output_data.stdout and output_data.show_output:
                stdout = output_data.stdout
                if len(stdout) > output_data.max_output_length:
                    stdout = stdout[:output_data.max_output_length] + "...(truncated)"
                format_dict["stdout"] = stdout + "\n" if stdout and not stdout.endswith("\n") else stdout or ""
            else:
                format_dict["stdout"] = ""
            
            # 標準エラーの処理
            if output_data.stderr and output_data.show_errors:
                stderr = output_data.stderr
                if len(stderr) > output_data.max_output_length:
                    stderr = stderr[:output_data.max_output_length] + "...(truncated)"
                format_dict["stderr"] = f"エラー: {stderr}\n" if stderr else ""
            else:
                format_dict["stderr"] = ""
            
            # その他の値
            format_dict.update({
                "return_code": str(output_data.return_code) if output_data.return_code is not None else "不明",
                "execution_time": output_data.execution_time or 0.0,
                "memory_usage": output_data.memory_usage or "不明"
            })
            
            # フォーマット実行
            result = OutputManagerFormatter.safe_format(
                template,
                format_dict,
                strict=strict,
                allow_missing=True
            )
            
            if strict and isinstance(result, FormatOperationResult):
                return FormatOperationResult(
                    success=result.success,
                    result=result.result,
                    missing_keys=result.missing_keys,
                    errors=result.errors,
                    warnings=result.warnings,
                    metadata={
                        **result.metadata,
                        "output_manager": True,
                        "template_used": template,
                        "stdout_length": len(output_data.stdout) if output_data.stdout else 0,
                        "stderr_length": len(output_data.stderr) if output_data.stderr else 0
                    }
                )
            else:
                return result[0] if isinstance(result, tuple) else result
                
        except Exception as e:
            error_msg = f"Failed to format output content: {e}"
            if strict:
                return FormatOperationResult(
                    success=False,
                    result=None,
                    missing_keys=[],
                    errors=[error_msg],
                    warnings=[],
                    metadata={"template": template, "output_data": str(output_data)}
                )
            else:
                raise ValueError(error_msg)
    
    @staticmethod
    def create_output_summary(output_data: OutputFormatData,
                            strict: bool = False) -> Union[Dict[str, Any], FormatOperationResult]:
        """出力データからサマリー情報を作成
        
        Args:
            output_data: 出力データ
            strict: Trueの場合、詳細な結果型を返す
            
        Returns:
            strict=Falseの場合: サマリー辞書
            strict=Trueの場合: FormatOperationResult
        """
        try:
            summary = {
                "has_output": bool(output_data.stdout),
                "has_errors": bool(output_data.stderr),
                "success": output_data.return_code == 0 if output_data.return_code is not None else None,
                "output_length": len(output_data.stdout) if output_data.stdout else 0,
                "error_length": len(output_data.stderr) if output_data.stderr else 0,
                "execution_time": output_data.execution_time,
                "memory_usage": output_data.memory_usage,
                "return_code": output_data.return_code
            }
            
            # 実行ステータスの判定
            if output_data.return_code is not None:
                if output_data.return_code == 0:
                    summary["status"] = "成功"
                else:
                    summary["status"] = f"エラー (コード: {output_data.return_code})"
            else:
                summary["status"] = "不明"
            
            if strict:
                return FormatOperationResult(
                    success=True,
                    result=None,
                    missing_keys=[],
                    errors=[],
                    warnings=[],
                    metadata={
                        "summary_keys": list(summary.keys()),
                        "output_data": str(output_data)
                    }
                )
            else:
                return summary
                
        except Exception as e:
            error_msg = f"Failed to create output summary: {e}"
            if strict:
                return FormatOperationResult(
                    success=False,
                    result=None,
                    missing_keys=[],
                    errors=[error_msg],
                    warnings=[],
                    metadata={"output_data": str(output_data)}
                )
            else:
                raise ValueError(error_msg)


# 互換性のためのエイリアス関数
def extract_output_data(result) -> OutputFormatData:
    """既存コードとの互換性維持"""
    return OutputManagerFormatter.extract_output_data(result, strict=False)


def should_show_output(request) -> bool:
    """既存コードとの互換性維持"""
    return OutputManagerFormatter.should_show_output(request, strict=False)


def format_output_content(output_data: OutputFormatData) -> str:
    """既存コードとの互換性維持"""
    return OutputManagerFormatter.format_output_content(output_data, strict=False)