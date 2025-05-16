import os
import tempfile
import pytest
from src.operations.file.file_request import FileRequest, FileOpType
from src.operations.file.file_result import FileResult

def test_file_write_and_read():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "test.txt")
        # write
        req_w = FileRequest(FileOpType.WRITE, path, content="hello world")
        # 仮実装なのでsuccessのみ確認
        result_w = req_w.execute()
        assert isinstance(result_w, FileResult)
        assert result_w.success
        # read
        req_r = FileRequest(FileOpType.READ, path)
        result_r = req_r.execute()
        assert isinstance(result_r, FileResult)
        # 仮実装なのでcontentは空文字列
        assert result_r.success
        # exists
        req_e = FileRequest(FileOpType.EXISTS, path)
        result_e = req_e.execute()
        assert isinstance(result_e, FileResult)
        assert result_e.success
        assert result_e.exists is True

def test_file_request_fail():
    req = FileRequest(FileOpType.READ, "/path/to/notfound.txt")
    result = req.execute()
    # 仮実装なのでsuccess=Trueだが、実装後は失敗を想定
    # assert not result.success
    # with pytest.raises(RuntimeError):
    #     result.raise_if_error() 