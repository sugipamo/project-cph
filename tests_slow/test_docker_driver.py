import pytest
from src.operations.mock.mock_docker_driver import MockDockerDriver, DummyDockerDriver
from src.operations.docker.docker_driver import LocalDockerDriver
from src.operations.result import OperationResult

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

def test_localdockerdriver_commands():
    driver = LocalDockerDriver()
    # build
    dockerfile_content = 'FROM python:3.8\n'
    result = driver.build(tag="t", options={"build_arg": "VAL"}, dockerfile_text=dockerfile_content)
    assert result.cmd == ["docker", "build", "-f", "-", "-t", "t", "--build-arg", "VAL", "."]
    # image_ls
    result = driver.image_ls()
    assert result.cmd == ["docker", "image", "ls"]
    # image_rm
    result = driver.image_rm("img")
    assert result.cmd == ["docker", "image", "rm", "img"]
    # ps
    result = driver.ps()
    assert result.cmd == ["docker", "ps"]
    result2 = driver.ps(all=True)
    assert result2.cmd == ["docker", "ps", "-a"]
    # inspect
    result = driver.inspect("img", type_="image")
    assert result.cmd == ["docker", "inspect", "--type", "image", "img"]
    # run_container
    result = driver.run_container("img", name="c", options={"env": "VAL"})
    assert result.cmd[:6] == ["docker", "run", "-d", "--env", "VAL", "--name"] or result.cmd[:6] == ["docker", "run", "-d", "--name", "c", "--env"]
    assert "img" in result.cmd
    # stop_container
    result = driver.stop_container("c")
    assert result.cmd == ["docker", "stop", "c"]
    # remove_container
    result = driver.remove_container("c")
    assert result.cmd == ["docker", "rm", "c"]
    # exec_in_container
    result = driver.exec_in_container("c", "ls -l")
    assert result.cmd[:3] == ["docker", "exec", "c"]
    assert "ls" in result.cmd and "-l" in result.cmd
    # get_logs
    result = driver.get_logs("c")
    assert result.cmd == ["docker", "logs", "c"]

def test_run_container():
    driver = LocalDockerDriver()
    result = driver.run_container("ubuntu:latest", name="c1", options={"d": None})
    assert "docker" in result.cmd and "run" in result.cmd and "ubuntu:latest" in result.cmd
    assert "--name" in result.cmd and "c1" in result.cmd

def test_stop_container():
    driver = LocalDockerDriver()
    result = driver.stop_container("c1")
    assert result.cmd == ["docker", "stop", "c1"]

def test_remove_container():
    driver = LocalDockerDriver()
    result = driver.remove_container("c1")
    assert result.cmd == ["docker", "rm", "c1"]

def test_exec_in_container():
    driver = LocalDockerDriver()
    result = driver.exec_in_container("c1", "ls -l")
    assert result.cmd[:3] == ["docker", "exec", "c1"]
    assert "ls" in result.cmd and "-l" in result.cmd

def test_get_logs():
    driver = LocalDockerDriver()
    result = driver.get_logs("c1")
    assert result.cmd == ["docker", "logs", "c1"]

def test_build():
    driver = LocalDockerDriver()
    dockerfile_content = 'FROM python:3.9\n'
    # -f - で標準入力を使うケース
    result = driver.build(tag="t1", options={"no_cache": None}, dockerfile_text=dockerfile_content)
    # コマンド内容の確認
    assert result.cmd[:4] == ["docker", "build", "-f", "-"]
    assert "-t" in result.cmd
    assert "t1" in result.cmd
    assert "." in result.cmd
    # --no-cacheが含まれる
    assert "--no-cache" in result.cmd

def test_image_ls():
    driver = LocalDockerDriver()
    result = driver.image_ls()
    assert result.cmd == ["docker", "image", "ls"]

def test_image_rm():
    driver = LocalDockerDriver()
    result = driver.image_rm("img1")
    assert result.cmd == ["docker", "image", "rm", "img1"]

def test_ps():
    driver = LocalDockerDriver()
    result = driver.ps()
    assert result.cmd == ["docker", "ps"]
    result2 = driver.ps(all=True)
    assert result2.cmd == ["docker", "ps", "-a"]

def test_inspect():
    driver = LocalDockerDriver()
    result = driver.inspect("c1")
    assert result.cmd[-1] == "c1"
    result2 = driver.inspect("c1", type_="container")
    assert "--type" in result2.cmd and "container" in result2.cmd

def test_cp_to_container():
    driver = LocalDockerDriver()
    result = driver.cp("host.txt", "cont.txt", "c1", to_container=True)
    assert result.cmd[:3] == ["docker", "cp", "host.txt"]
    assert "c1:cont.txt" in result.cmd

def test_cp_from_container():
    driver = LocalDockerDriver()
    result = driver.cp("cont.txt", "host.txt", "c1", to_container=False)
    assert result.cmd[:3] == ["docker", "cp", "c1:cont.txt"]
    assert "host.txt" in result.cmd

def test_localdockerdriver_build_stdin():
    """
    LocalDockerDriver.build() で dockerfile_text を渡した場合、
    ShellUtil.run_subprocess の inputdata に正しく渡るかをテスト
    """
    from src.operations.docker.docker_driver import LocalDockerDriver
    from src.operations.shell import shell_util
    # ShellUtil.run_subprocessを一時的に差し替え
    orig_run_subprocess = shell_util.ShellUtil.run_subprocess
    called = {}
    def fake_run_subprocess(cmd, cwd=None, env=None, inputdata=None, timeout=None):
        called.update(dict(cmd=cmd, cwd=cwd, env=env, inputdata=inputdata, timeout=timeout))
        class Completed:
            stdout = "build ok"
            stderr = ""
            returncode = 0
        return Completed()
    shell_util.ShellUtil.run_subprocess = fake_run_subprocess
    try:
        driver = LocalDockerDriver()
        dockerfile_content = 'FROM python:3.10\nRUN echo "hello"\n'
        result = driver.build(tag="t2", options={}, dockerfile_text=dockerfile_content)
        print(called)  # デバッグ用
        assert called["inputdata"] == dockerfile_content
        assert result.stdout == "build ok"
    finally:
        shell_util.ShellUtil.run_subprocess = orig_run_subprocess 

def test_build_raises_on_none_dockerfile_text():
    driver = LocalDockerDriver()
    with pytest.raises(ValueError):
        driver.build(None, tag="t")

def test_build_with_short_and_long_options():
    driver = LocalDockerDriver()
    dockerfile_content = 'FROM python:3.8\n'
    result = driver.build(dockerfile_content, tag="t", options={"q": None, "no_cache": None})
    assert "-q" in result.cmd
    assert "--no-cache" in result.cmd

def test_build_show_output_false():
    driver = LocalDockerDriver()
    dockerfile_content = 'FROM python:3.8\n'
    result = driver.build(dockerfile_content, tag="t", options={"no_cache": None}, show_output=False)
    assert result.cmd[:4] == ["docker", "build", "-f", "-"]
    assert "-t" in result.cmd
    assert "t" in result.cmd
    assert "." in result.cmd
    assert "--no-cache" in result.cmd
    # result.stdout の内容は環境依存のため検証しない 
