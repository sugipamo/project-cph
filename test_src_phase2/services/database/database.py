from core.logger.logger import Logger
from core.config.config import Config

class Database:

    def __init__(self):
        self.logger = Logger()
        self.config = Config()

    def connect(self):
        self.logger.log('Connecting to database...')
        return f'Connected with {self.config.get_retry_count()} retries'