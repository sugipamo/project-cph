import pytest
from src.operations.docker.docker_driver import MockDockerDriver, DummyDockerDriver, LocalDockerDriver

# MockDockerDriverのテスト

def test_mockdockerdriver_all_methods():
    driver = MockDockerDriver()
    # build
    assert driver.build("./context", tag="myimg:latest", dockerfile="Dockerfile") == "mock_build_myimg:latest"
    # image_ls
    assert driver.image_ls() == ["mock_image1", "mock_image2"]
    # image_rm
    assert driver.image_rm("myimg:latest") == "mock_rm_myimg:latest"
    # ps
    assert driver.ps() == ["mock_container1", "mock_container2"]
    # inspect
    assert driver.inspect("myimg:latest", type_="image") == {"mock_inspect": "myimg:latest", "type": "image"}
    # run_container
    assert driver.run_container("python:3.11", name="c1").stdout == "mock_container_c1"
    # stop_container
    assert driver.stop_container("c1").stdout is None
    # remove_container
    assert driver.remove_container("c1").stdout is None
    # exec_in_container
    assert driver.exec_in_container("c1", "ls -l").stdout == "mock_exec_result_c1_ls -l"
    # get_logs
    assert driver.get_logs("c1").stdout == "mock_logs_c1"

# DummyDockerDriverのテスト

def test_dummydockerdriver_all_methods():
    driver = DummyDockerDriver()
    assert driver.build("./context") is None
    assert driver.image_ls() == []
    assert driver.image_rm("img") is None
    assert driver.ps() == []
    assert driver.inspect("img") is None
    assert driver.run_container("img") is None
    assert driver.stop_container("c") is None
    assert driver.remove_container("c") is None
    assert driver.exec_in_container("c", "ls") is None
    assert driver.get_logs("c") is None

# LocalDockerDriverのコマンド生成テスト（ShellRequestをmonkeypatch）
import types
from src.operations.shell.shell_request import ShellRequest

def fake_execute(self):
    # コマンド内容を返すだけ
    return self.cmd

@pytest.fixture(autouse=True)
def patch_shellrequest_execute(monkeypatch):
    monkeypatch.setattr(ShellRequest, "execute", fake_execute)

def test_localdockerdriver_commands():
    driver = LocalDockerDriver()
    # build
    assert driver.build("./ctx", tag="t", dockerfile="Df", options={"build_arg": "VAL"}) == ["docker", "build", "-t", "t", "-f", "Df", "--build-arg", "VAL", "./ctx"]
    # image_ls
    assert driver.image_ls() == ["docker", "image", "ls"]
    # image_rm
    assert driver.image_rm("img") == ["docker", "image", "rm", "img"]
    # ps
    assert driver.ps() == ["docker", "ps"]
    assert driver.ps(all=True) == ["docker", "ps", "-a"]
    # inspect
    assert driver.inspect("img", type_="image") == ["docker", "inspect", "--type", "image", "img"]
    # run_container
    assert driver.run_container("img", name="c", options={"env": "VAL"}) == ["docker", "run", "-d", "--name", "c", "--env", "VAL", "img"]
    # stop_container
    assert driver.stop_container("c") == ["docker", "stop", "c"]
    # remove_container
    assert driver.remove_container("c") == ["docker", "rm", "c"]
    # exec_in_container
    assert driver.exec_in_container("c", "ls -l") == ["docker", "exec", "c", "ls", "-l"]
    # get_logs
    assert driver.get_logs("c") == ["docker", "logs", "c"] 