import os

class Opener:
    @property
    def source_path(self):
        return self._source_path
    @source_path.setter
    def source_path(self, value):
        self._source_path = value
    @property
    def url(self):
        return self._url
    @url.setter
    def url(self, value):
        self._url = value
    def open_editor(self):
        import subprocess
        print(self.source_path)
        subprocess.call(["code", self.source_path], env=os.environ.copy())
        subprocess.call(["cursor", self.source_path], env=os.environ.copy())
    def open_browser(self):
        import webbrowser
        webbrowser.open(self.url)

class MockOpener(Opener):
    def __init__(self):
        self.opened_paths = []
        self.opened_urls = []
        self._source_path = None
        self._url = None
    def open_editor(self):
        self.opened_paths.append(self.source_path)
    def open_browser(self):
        self.opened_urls.append(self.url) 