import pytest
import hashlib
from src.env.resource.utils.docker_naming import (
    get_image_name, get_container_name, get_oj_image_name, get_oj_container_name
)


def test_get_image_name_without_dockerfile():
    result = get_image_name("python")
    assert result == "python"


def test_get_image_name_with_dockerfile():
    dockerfile_text = "FROM python:3.8\nRUN echo hello"
    expected_hash = hashlib.sha256(dockerfile_text.encode("utf-8")).hexdigest()[:12]
    result = get_image_name("python", dockerfile_text)
    assert result == f"python_{expected_hash}"


def test_get_container_name_without_dockerfile():
    result = get_container_name("python")
    assert result == "cph_python"


def test_get_container_name_with_dockerfile():
    dockerfile_text = "FROM python:3.8\nRUN echo hello"
    expected_hash = hashlib.sha256(dockerfile_text.encode("utf-8")).hexdigest()[:12]
    result = get_container_name("python", dockerfile_text)
    assert result == f"cph_python_{expected_hash}"


def test_get_oj_image_name_without_dockerfile():
    result = get_oj_image_name()
    assert result == "ojtools"


def test_get_oj_image_name_with_dockerfile():
    oj_dockerfile_text = "FROM python:3.9\nRUN echo oj"
    expected_hash = hashlib.sha256(oj_dockerfile_text.encode("utf-8")).hexdigest()[:12]
    result = get_oj_image_name(oj_dockerfile_text)
    assert result == f"ojtools_{expected_hash}"


def test_get_oj_container_name_without_dockerfile():
    result = get_oj_container_name()
    assert result == "cph_ojtools"


def test_get_oj_container_name_with_dockerfile():
    oj_dockerfile_text = "FROM python:3.9\nRUN echo oj"
    expected_hash = hashlib.sha256(oj_dockerfile_text.encode("utf-8")).hexdigest()[:12]
    result = get_oj_container_name(oj_dockerfile_text)
    assert result == f"cph_ojtools_{expected_hash}"


def test_get_image_name_empty_dockerfile():
    result = get_image_name("python", "")
    assert result == "python"


def test_get_image_name_none_dockerfile():
    result = get_image_name("python", None)
    assert result == "python"