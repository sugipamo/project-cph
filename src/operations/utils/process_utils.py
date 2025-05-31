"""
プロセス実行に関するユーティリティ関数
"""
import subprocess
import signal
import os
from typing import List, Optional, Dict, Any

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


class ProcessUtil:
    """プロセス実行のユーティリティクラス"""
    
    @staticmethod
    def run_command(cmd: List[str], 
                   cwd: Optional[str] = None,
                   env: Optional[Dict[str, str]] = None,
                   inputdata: Optional[str] = None,
                   timeout: Optional[float] = None,
                   capture_output: bool = True,
                   text: bool = True) -> subprocess.CompletedProcess:
        """
        コマンドを実行する
        
        Args:
            cmd: 実行するコマンド
            cwd: 作業ディレクトリ
            env: 環境変数
            inputdata: 標準入力に渡すデータ
            timeout: タイムアウト（秒）
            capture_output: 出力をキャプチャするか
            text: テキストモードで実行するか
            
        Returns:
            実行結果
        """
        return subprocess.run(
            cmd,
            cwd=cwd,
            env=env,
            input=inputdata,
            timeout=timeout,
            capture_output=capture_output,
            text=text
        )
    
    @staticmethod
    def run_command_async(cmd: List[str],
                         cwd: Optional[str] = None,
                         env: Optional[Dict[str, str]] = None,
                         stdin: Any = None,
                         stdout: Any = None,
                         stderr: Any = None) -> subprocess.Popen:
        """
        コマンドを非同期で実行する
        
        Args:
            cmd: 実行するコマンド
            cwd: 作業ディレクトリ
            env: 環境変数
            stdin: 標準入力
            stdout: 標準出力
            stderr: 標準エラー
            
        Returns:
            Popenオブジェクト
        """
        return subprocess.Popen(
            cmd,
            cwd=cwd,
            env=env,
            stdin=stdin,
            stdout=stdout,
            stderr=stderr,
            text=True
        )
    
    @staticmethod
    def kill_process_tree(pid: int, signal_type: int = signal.SIGTERM, timeout: float = 5.0):
        """
        プロセスツリーを終了する
        
        Args:
            pid: プロセスID
            signal_type: 送信するシグナル
            timeout: 強制終了までの待機時間
        """
        if not HAS_PSUTIL:
            # psutilがない場合は単純にkillを送信
            try:
                os.kill(pid, signal_type)
            except ProcessLookupError:
                pass
            return
            
        try:
            parent = psutil.Process(pid)
            children = parent.children(recursive=True)
            
            # 子プロセスから順番に終了
            for child in children:
                try:
                    child.send_signal(signal_type)
                except psutil.NoSuchProcess:
                    pass
            
            # 親プロセスを終了
            try:
                parent.send_signal(signal_type)
            except psutil.NoSuchProcess:
                return
            
            # 正常終了を待機
            gone, alive = psutil.wait_procs(children + [parent], timeout=timeout)
            
            # まだ生きているプロセスを強制終了
            for proc in alive:
                try:
                    proc.kill()
                except psutil.NoSuchProcess:
                    pass
                    
        except psutil.NoSuchProcess:
            # プロセスが既に存在しない
            pass
    
    @staticmethod
    def is_process_running(pid: int) -> bool:
        """
        プロセスが実行中かどうかを確認する
        
        Args:
            pid: プロセスID
            
        Returns:
            実行中の場合True
        """
        if not HAS_PSUTIL:
            try:
                os.kill(pid, 0)  # シグナル0で存在確認
                return True
            except ProcessLookupError:
                return False
        
        try:
            return psutil.Process(pid).is_running()
        except psutil.NoSuchProcess:
            return False
    
    @staticmethod
    def get_process_info(pid: int) -> Optional[Dict[str, Any]]:
        """
        プロセス情報を取得する
        
        Args:
            pid: プロセスID
            
        Returns:
            プロセス情報の辞書
        """
        if not HAS_PSUTIL:
            return {'pid': pid, 'available': False}
        
        try:
            proc = psutil.Process(pid)
            return {
                'pid': proc.pid,
                'name': proc.name(),
                'cmdline': proc.cmdline(),
                'status': proc.status(),
                'cpu_percent': proc.cpu_percent(),
                'memory_info': proc.memory_info(),
                'create_time': proc.create_time()
            }
        except psutil.NoSuchProcess:
            return None
    
    @staticmethod
    def find_processes_by_name(name: str) -> List[int]:
        """
        プロセス名からプロセスIDのリストを取得する
        
        Args:
            name: プロセス名
            
        Returns:
            プロセスIDのリスト
        """
        pids = []
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if proc.info['name'] == name:
                    pids.append(proc.info['pid'])
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        return pids
    
    @staticmethod
    def wait_for_process_completion(pid: int, timeout: Optional[float] = None) -> bool:
        """
        プロセスの完了を待機する
        
        Args:
            pid: プロセスID
            timeout: タイムアウト（秒）
            
        Returns:
            正常に完了した場合True
        """
        try:
            proc = psutil.Process(pid)
            proc.wait(timeout=timeout)
            return True
        except (psutil.NoSuchProcess, psutil.TimeoutExpired):
            return False
    
    @staticmethod
    def get_system_memory_usage() -> Dict[str, float]:
        """
        システムのメモリ使用状況を取得する
        
        Returns:
            メモリ使用状況の辞書
        """
        memory = psutil.virtual_memory()
        return {
            'total': memory.total,
            'available': memory.available,
            'used': memory.used,
            'percent': memory.percent
        }
    
    @staticmethod
    def get_system_cpu_usage() -> float:
        """
        システムのCPU使用率を取得する
        
        Returns:
            CPU使用率（パーセント）
        """
        return psutil.cpu_percent(interval=1)