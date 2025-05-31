import pathlib
import subprocess
import contextlib
import io
import traceback

class PythonUtils:
    @staticmethod
    def is_script_file(code_or_file):
        """
        code_or_file: list[str]（1要素ならファイル名の可能性あり）
        ファイルならTrue, そうでなければFalse
        """
        return len(code_or_file) == 1 and pathlib.Path(code_or_file[0]).is_file()

    @staticmethod
    def run_script_file(filename, cwd=None):
        result = subprocess.run([
            subprocess.getoutput('which python3') or 'python3', filename
        ], capture_output=True, text=True, cwd=cwd)
        return result.stdout, result.stderr, result.returncode

    @staticmethod
    def run_code_string(code, cwd=None):
        buf_out = io.StringIO()
        buf_err = io.StringIO()
        returncode = 0
        with contextlib.redirect_stdout(buf_out), contextlib.redirect_stderr(buf_err):
            try:
                exec(code, {})
            except Exception:
                traceback.print_exc(file=buf_err)
                returncode = 1
        return buf_out.getvalue(), buf_err.getvalue(), returncode 