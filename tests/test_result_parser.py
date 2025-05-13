from src.test_result_parser import TestResultParser

class DummyResult:
    def __init__(self, returncode=0, stdout='', stderr=''):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr

def test_parse_success():
    result = DummyResult(returncode=0, stdout='ok', stderr='')
    ok, out, err = TestResultParser.parse(result)
    assert ok is True
    assert out == 'ok'
    assert err == ''

def test_parse_failure():
    result = DummyResult(returncode=1, stdout='', stderr='fail')
    ok, out, err = TestResultParser.parse(result)
    assert ok is False
    assert out == ''
    assert err == 'fail'

def test_parse_missing_attrs():
    class NoAttrs: pass
    result = NoAttrs()
    ok, out, err = TestResultParser.parse(result)
    assert ok is False
    assert out == ''
    assert err == '' 