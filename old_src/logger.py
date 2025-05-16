class Logger:
    @staticmethod
    def info(msg):
        print(f"[INFO] {msg}")

    @staticmethod
    def warn(msg):
        print(f"[WARN] {msg}")

    @staticmethod
    def error(msg):
        print(f"[ERROR] {msg}") 