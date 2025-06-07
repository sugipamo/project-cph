import pytest

from src.infrastructure.di_container import DIContainer


def test_register_and_resolve():
    container = DIContainer()
    container.register("int_provider", lambda: 42)
    container.register("str_provider", lambda: "hello")
    assert container.resolve("int_provider") == 42
    assert container.resolve("str_provider") == "hello"
    # 複数回resolveしても新しいインスタンスが返る（関数が呼ばれる）
    assert container.resolve("int_provider") == 42

def test_resolve_unregistered_key():
    container = DIContainer()
    with pytest.raises(ValueError) as e:
        container.resolve("not_registered")
    assert "not_registered" in str(e.value)
