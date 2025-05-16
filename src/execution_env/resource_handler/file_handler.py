
class BaseFileHandler:
    def __init__(self, config: dict):
        self.config = config

class DockerFileHandler(BaseFileHandler):
    pass

class LocalFileHandler(BaseFileHandler):
    pass