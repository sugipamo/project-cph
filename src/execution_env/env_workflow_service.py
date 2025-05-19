from typing import List
from src.execution_env.env_resource_controller import EnvResourceController
from src.execution_env.env_context_loader import load_env_context_from_language_env, load_env_json
from src.execution_env.env_context_loader import EnvContext, OjContext
import copy
from src.operations.composite_request import CompositeRequest

class EnvWorkflowService:
    def __init__(self):
        pass

    def generate_run_requests(self, ):
        # TODO
        # Controllerを呼び出し
        # jsonの設定をもとにrequestを生成
        # requestはsrc/operationsを参照
