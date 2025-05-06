class DockerPathMapper:
    def __init__(self, host_root, container_root):
        self.host_root = host_root
        self.container_root = container_root

    def to_container_path(self, host_path: str) -> str:
        return str(host_path).replace(self.host_root, self.container_root, 1)

    def to_host_path(self, container_path: str) -> str:
        return str(container_path).replace(self.container_root, self.host_root, 1) 