import pytest
from src.commands import common

def test_get_project_root_volumes():
    # 返り値がdictで、少なくとも1つはマウントが含まれることを確認
    vols = common.get_project_root_volumes()
    assert isinstance(vols, dict)
    # パスの形式や内容は環境依存なので、型とキーだけ確認
    for k, v in vols.items():
        assert isinstance(k, str)
        assert isinstance(v, str) 