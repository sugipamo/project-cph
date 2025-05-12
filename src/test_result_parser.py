class TestResultParser:
    @staticmethod
    def parse(result):
        ok = getattr(result, 'returncode', 1) == 0
        stdout = getattr(result, 'stdout', '')
        stderr = getattr(result, 'stderr', '')
        return ok, stdout, stderr 