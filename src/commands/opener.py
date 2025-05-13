import os

class Opener:
    def open_editor(self, path: str, language: str = None):
        import subprocess
        print(path)
        subprocess.call(["code", path], env=os.environ.copy())
        import subprocess
        subprocess.call(["cursor", path], env=os.environ.copy())
    def open_browser(self, url: str):
        import webbrowser
        webbrowser.open(url)

class MockOpener(Opener):
    def __init__(self):
        self.opened_paths = []
        self.opened_urls = []
    def open_editor(self, path: str, language: str = None):
        self.opened_paths.append(path)
    def open_browser(self, url: str):
        self.opened_urls.append(url) 