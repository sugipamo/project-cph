class BaseCommandRequestFactory:
    def __init__(self, controller):
        self.controller = controller

    def create_request(self, run_step):
        raise NotImplementedError 