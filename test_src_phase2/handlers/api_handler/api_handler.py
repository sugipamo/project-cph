from services.database.database import Database

class APIHandler:

    def __init__(self):
        self.db = Database()

    def handle_request(self):
        result = self.db.connect()
        return f'API: {result}'