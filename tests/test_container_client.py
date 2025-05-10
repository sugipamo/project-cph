import pytest
from unittest.mock import patch
from src.execution_client.container.client import ContainerClient, AbstractContainerClient
import json

def make_inspect_result(obj):
    return json.dumps([obj])

@patch("subprocess.run")
def test_inspect_container(mock_run):
    mock_run.return_value.returncode = 0
    mock_run.return_value.stdout = make_inspect_result({"Id": "abc123", "Name": "test"})
    client = ContainerClient()
    result = client.inspect_container("test")
    assert result["Id"] == "abc123"
    assert result["Name"] == "test"

@patch("subprocess.run")
def test_inspect_image(mock_run):
    mock_run.return_value.returncode = 0
    mock_run.return_value.stdout = make_inspect_result({"Id": "img456", "RepoTags": ["test:latest"]})
    client = ContainerClient()
    result = client.inspect_image("test:latest")
    assert result["Id"] == "img456"
    assert "test:latest" in result["RepoTags"]

@patch("subprocess.run")
def test_get_container_logs(mock_run):
    mock_run.return_value.returncode = 0
    mock_run.return_value.stdout = "log1\nlog2\n"
    client = ContainerClient()
    logs = client.get_container_logs("test")
    assert "log1" in logs and "log2" in logs

@patch("subprocess.run")
def test_get_container_logs_with_tail(mock_run):
    mock_run.return_value.returncode = 0
    mock_run.return_value.stdout = "lastlog\n"
    client = ContainerClient()
    logs = client.get_container_logs("test", tail=1)
    assert "lastlog" in logs

@patch("subprocess.run")
def test_run_container_with_options(mock_run):
    mock_run.return_value.returncode = 0
    mock_run.return_value.stdout = "container_id"
    client = ContainerClient()
    cid = client.run_container(
        name="test",
        image="img",
        command=["echo", "hello"],
        volumes={"/host": "/cont"},
        env={"ENV1": "VAL1"},
        ports={8080: 80},
        cpus=1.5,
        memory="512m"
    )
    assert cid == "container_id"
    called_args = mock_run.call_args[0][0]
    assert "-v" in called_args and "/host:/cont" in called_args
    assert "-e" in called_args and "ENV1=VAL1" in called_args
    assert "-p" in called_args and "8080:80" in called_args
    assert "--cpus" in called_args and "1.5" in called_args
    assert "--memory" in called_args and "512m" in called_args

@patch("subprocess.run")
def test_container_exists(mock_run):
    mock_run.return_value.returncode = 0
    mock_run.return_value.stdout = "test1\ntest2\n"
    client = ContainerClient()
    assert client.container_exists("test1")
    assert not client.container_exists("notfound")

@patch("subprocess.run")
def test_image_exists(mock_run):
    mock_run.return_value.returncode = 0
    mock_run.return_value.stdout = "img1\nimg2\n"
    client = ContainerClient()
    assert client.image_exists("img2")
    assert not client.image_exists("notfound")

@patch("subprocess.run")
def test_copy_to_container(mock_run):
    mock_run.return_value.returncode = 0
    client = ContainerClient()
    assert client.copy_to_container("test", "/host/file", "/cont/file")
    mock_run.return_value.returncode = 1
    assert not client.copy_to_container("test", "/host/file", "/cont/file")

@patch("subprocess.run")
def test_copy_from_container(mock_run):
    mock_run.return_value.returncode = 0
    client = ContainerClient()
    assert client.copy_from_container("test", "/cont/file", "/host/file")
    mock_run.return_value.returncode = 1
    assert not client.copy_from_container("test", "/cont/file", "/host/file")

@patch("subprocess.run")
def test_exec_in_container(mock_run):
    mock_run.return_value.returncode = 0
    mock_run.return_value.stdout = "output"
    client = ContainerClient()
    result = client.exec_in_container("test", ["echo", "hello"])
    assert result.returncode == 0
    assert result.stdout == "output"
    # エラー時
    mock_run.return_value.returncode = 1
    mock_run.return_value.stderr = "error"
    result = client.exec_in_container("test", ["false"])
    assert result.returncode == 1

@patch("subprocess.run")
def test_list_containers(mock_run):
    mock_run.return_value.returncode = 0
    mock_run.return_value.stdout = "cph_test1\ncph_test2\nother\n"
    client = ContainerClient()
    all_names = client.list_containers()
    assert "cph_test1" in all_names and "cph_test2" in all_names and "other" in all_names
    filtered = client.list_containers(prefix="cph_")
    assert set(filtered) == {"cph_test1", "cph_test2"}

@patch("subprocess.run")
def test_is_container_running(mock_run):
    mock_run.return_value.returncode = 0
    mock_run.return_value.stdout = "true"
    client = ContainerClient()
    assert client.is_container_running("test")
    mock_run.return_value.stdout = "false"
    assert not client.is_container_running("test")
    mock_run.return_value.returncode = 1
    assert not client.is_container_running("test") 