from src.operations.base_request import BaseRequest

class DriverBoundRequest(BaseRequest):
    def __init__(self, req, driver):
        super().__init__(name=getattr(req, 'name', None), debug_tag=getattr(req, 'debug_tag', None))
        self.req = req
        self.driver = driver
    def execute(self, driver=None):
        # driver引数より自身のdriver属性を優先
        return self.req.execute(driver=self.driver)
    @property
    def operation_type(self):
        return getattr(self.req, 'operation_type', None) 