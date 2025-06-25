from constants import API_VERSION

class Logger:

    def __init__(self):
        self.version = API_VERSION

    def log(self, message):
        print(f'[v{self.version}] {message}')