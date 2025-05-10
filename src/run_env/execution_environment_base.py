from abc import ABC, abstractmethod

class RunExecutionEnvironment(ABC):
    @abstractmethod
    def prepare_source_code(self, contest_name, problem_name, language_name):
        pass

    @abstractmethod
    def prepare_test_cases(self, contest_name, problem_name):
        pass

    @abstractmethod
    def to_container_path(self, host_path: str) -> str:
        pass

    @abstractmethod
    def to_host_path(self, container_path: str) -> str:
        pass

    @abstractmethod
    def run_test_case(self, language_name, container, in_file, source_path, retry=2):
        pass 