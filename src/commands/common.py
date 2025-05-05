# ここには他の共通関数のみを残す

def get_project_root_volumes():
    import os
    project_root = os.path.abspath(".")
    volumes = {
        project_root: "/workspace"
    }
    return volumes 