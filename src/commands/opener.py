class Opener:
    def open_editor(self, path: str, language: str = None):
        # 言語によって開くファイルを切り替え
        if language == "rust":
            main_file = f"{path}/src/main.rs"
        else:
            main_file = f"{path}/main.py"
        try:
            import subprocess
            subprocess.Popen(["code", "--reuse-window", main_file])
        except Exception as e:
            print(f"[警告] VSCode起動失敗: {e}")
        try:
            import subprocess
            subprocess.Popen(["cursor", "--reuse-window", main_file])
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
        if language == "rust":
            main_file = f"{path}/src/main.rs"
        else:
            main_file = f"{path}/main.py"
        self.opened_paths.append(main_file)
    def open_browser(self, url: str):
        self.opened_urls.append(url) 