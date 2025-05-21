from pathlib import Path

class PathEnvironmentChecker:
    def __init__(self, workspace_path):
        self.workspace_path = Path(workspace_path).resolve()

    def is_in_container(self, path: str) -> bool:
        p = Path(path).resolve()
        if p.is_absolute():
            target = p.resolve()
        else:
            target = (self.workspace_path / p).resolve()
        try:
            target.relative_to(self.workspace_path)
            return True
        except ValueError:
            return False 