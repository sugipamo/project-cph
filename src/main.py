"""Main entry point for the CPH application
"""
from src.cli.cli_app import main
from src.infrastructure.build_infrastructure import build_infrastructure
from src.infrastructure.di_container import DIKey

if __name__ == "__main__":
    infrastructure = build_infrastructure()
    sys_provider = infrastructure.resolve(DIKey.SYS_PROVIDER)
    main(sys_provider.get_argv()[1:], sys_provider.exit)
