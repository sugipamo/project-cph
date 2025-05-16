class FileResult:
    def __init__(self, success: bool, content: str = None, exists: bool = None):
        self.success = success
        self.content = content
        self.exists = exists 