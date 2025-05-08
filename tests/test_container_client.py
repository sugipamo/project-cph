import pytest
from unittest.mock import patch
from src.container.client import ContainerClient
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