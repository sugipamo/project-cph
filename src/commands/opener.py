class Opener:
    def open_editor(self, path: str, language: str = None):
        try:
            import subprocess
            subprocess.Popen(["code", "--reuse-window", path])
        except Exception as e:
            print(f"[警告] VSCode起動失敗: {e}")
        try:
            import subprocess
            subprocess.Popen(["cursor", "--reuse-window", path])
        except Exception as e:
            print(f"[警告] Cursor起動失敗: {e}")
    def open_browser(self, url: str):
        try:
            import webbrowser
            webbrowser.open(url)
        except Exception as e:
            print(f"[警告] ブラウザでページを開けませんでした: {e}")

class MockOpener(Opener):
    def __init__(self):
        self.opened_paths = []
        self.opened_urls = []
    def open_editor(self, path: str, language: str = None):
        self.opened_paths.append(path)
    def open_browser(self, url: str):
        self.opened_urls.append(url) 