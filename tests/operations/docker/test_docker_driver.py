import pytest
from src.operations.mock.mock_docker_driver import MockDockerDriver, DummyDockerDriver
from src.operations.docker.docker_driver import LocalDockerDriver

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

@pytest.fixture(autouse=True)
def patch_shellrequest_execute(monkeypatch):
    def fake_execute(self, driver=None):
        return self.cmd
    monkeypatch.setattr("src.operations.shell.shell_request.ShellRequest.execute", fake_execute)

def test_localdockerdriver_commands():
    driver = LocalDockerDriver()
    # build
    assert driver.build("./ctx", tag="t", dockerfile="Df", options={"build_arg": "VAL"}) == ["docker", "build", "--build-arg", "VAL", "-t", "t", "-f", "Df", "./ctx"]
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
    assert driver.run_container("img", name="c", options={"env": "VAL"}) == ["docker", "run", "-d", "--env", "VAL", "--name", "c", "img"]
    # stop_container
    assert driver.stop_container("c") == ["docker", "stop", "c"]
    # remove_container
    assert driver.remove_container("c") == ["docker", "rm", "c"]
    # exec_in_container
    assert driver.exec_in_container("c", "ls -l") == ["docker", "exec", "c", "ls", "-l"]
    # get_logs
    assert driver.get_logs("c") == ["docker", "logs", "c"]

def test_run_container():
    driver = LocalDockerDriver()
    cmd = driver.run_container("ubuntu:latest", name="c1", options={"d": None})
    assert "docker" in cmd and "run" in cmd and "ubuntu:latest" in cmd
    assert "--name" in cmd and "c1" in cmd

def test_stop_container():
    driver = LocalDockerDriver()
    cmd = driver.stop_container("c1")
    assert cmd[:3] == ["docker", "stop", "c1"]

def test_remove_container():
    driver = LocalDockerDriver()
    cmd = driver.remove_container("c1")
    assert cmd[:3] == ["docker", "rm", "c1"]

def test_exec_in_container():
    driver = LocalDockerDriver()
    cmd = driver.exec_in_container("c1", "ls -l")
    assert cmd[:3] == ["docker", "exec", "c1"]
    assert "ls" in cmd and "-l" in cmd

def test_get_logs():
    driver = LocalDockerDriver()
    cmd = driver.get_logs("c1")
    assert cmd[:3] == ["docker", "logs", "c1"]

def test_build():
    driver = LocalDockerDriver()
    cmd = driver.build(".", tag="t1", dockerfile="Dockerfile", options={"no_cache": None})
    assert "docker" in cmd and "build" in cmd and "." in cmd
    assert "-t" in cmd and "t1" in cmd
    assert "-f" in cmd and "Dockerfile" in cmd
    assert "--no-cache" in cmd

def test_image_ls():
    driver = LocalDockerDriver()
    cmd = driver.image_ls()
    assert cmd == ["docker", "image", "ls"]

def test_image_rm():
    driver = LocalDockerDriver()
    cmd = driver.image_rm("img1")
    assert cmd == ["docker", "image", "rm", "img1"]

def test_ps():
    driver = LocalDockerDriver()
    cmd = driver.ps()
    assert cmd == ["docker", "ps"]
    cmd2 = driver.ps(all=True)
    assert cmd2 == ["docker", "ps", "-a"]

def test_inspect():
    driver = LocalDockerDriver()
    cmd = driver.inspect("c1")
    assert cmd[-1] == "c1"
    cmd2 = driver.inspect("c1", type_="container")
    assert "--type" in cmd2 and "container" in cmd2

def test_cp_to_container():
    driver = LocalDockerDriver()
    cmd = driver.cp("host.txt", "cont.txt", "c1", to_container=True)
    assert cmd[:3] == ["docker", "cp", "host.txt"]
    assert "c1:cont.txt" in cmd

def test_cp_from_container():
    driver = LocalDockerDriver()
    cmd = driver.cp("cont.txt", "host.txt", "c1", to_container=False)
    assert cmd[:3] == ["docker", "cp", "c1:cont.txt"]
    assert "host.txt" in cmd 