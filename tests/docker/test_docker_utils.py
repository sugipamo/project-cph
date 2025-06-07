from src.shared.utils.docker.docker_utils import DockerUtils

def test_build_docker_cmd_basic():
    cmd = DockerUtils.build_docker_cmd(["docker", "run"], options={"name": "mycontainer", "d": None}, positional_args=["ubuntu:latest"])
    assert "--name" in cmd
    assert "mycontainer" in cmd
    assert "-d" in cmd
    assert "ubuntu:latest" in cmd

def test_build_docker_cmd_no_options():
    cmd = DockerUtils.build_docker_cmd(["docker", "ps"])
    assert cmd == ["docker", "ps"]

def test_build_docker_cmd_short_option():
    cmd = DockerUtils.build_docker_cmd(["docker", "run"], options={"a": "b"})
    assert "-a" in cmd and "b" in cmd

def test_build_docker_cmd_long_option():
    cmd = DockerUtils.build_docker_cmd(["docker", "run"], options={"rm": None})
    assert "--rm" in cmd

def test_parse_image_tag_with_tag():
    image, tag = DockerUtils.parse_image_tag("ubuntu:20.04")
    assert image == "ubuntu"
    assert tag == "20.04"

def test_parse_image_tag_without_tag():
    image, tag = DockerUtils.parse_image_tag("ubuntu")
    assert image == "ubuntu"
    assert tag is None 