import time
from src.logger import Logger

class Timer:
    def __init__(self, label=None):
        self.label = label
        self.start_time = None
        self.end_time = None
        self.elapsed = None

    def __enter__(self):
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.perf_counter()
        self.elapsed = self.end_time - self.start_time
        if self.label:
            Logger.info(f"{self.label} took {self.elapsed:.4f} seconds")
        else:
            Logger.info(f"Elapsed time: {self.elapsed:.4f} seconds") 