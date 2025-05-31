from src.context.execution_context import ExecutionContext

class EnvResourceController:
    def __init__(self, env_context: ExecutionContext, file_handler, run_handler, const_handler=None):
        self.env_context = env_context
        self.language_name = env_context.language
        self.env_type = env_context.env_type
        self.const_handler = const_handler
        self.run_handler = run_handler
        self.file_handler = file_handler

    def create_process_options(self, cmd: list):
        return self.run_handler.create_process_options(cmd)

    def read_file(self, relative_path: str) -> str:
        return self.file_handler.read(relative_path)

    def write_file(self, relative_path: str, content: str):
        return self.file_handler.write(relative_path, content)

    def file_exists(self, relative_path: str) -> bool:
        return self.file_handler.exists(relative_path)

    def remove_file(self, relative_path: str):
        return self.file_handler.remove(relative_path)

    def move_file(self, src_path: str, dst_path: str):
        return self.file_handler.move(src_path, dst_path)

    def copytree(self, src_path: str, dst_path: str):
        return self.file_handler.copytree(src_path, dst_path)

    def rmtree(self, dir_path: str):
        return self.file_handler.rmtree(dir_path)

    def copy_file(self, src_path: str, dst_path: str):
        return self.file_handler.copy(src_path, dst_path)