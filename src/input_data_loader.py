class InputDataLoader:
    @staticmethod
    def load(file_operator, host_in_file, host_in_file_path):
        if file_operator is not None:
            if host_in_file and file_operator.exists(host_in_file):
                with file_operator.open(host_in_file, "r", encoding="utf-8") as f:
                    return f.read()
            elif file_operator.exists(host_in_file_path):
                with file_operator.open(host_in_file_path, "r", encoding="utf-8") as f:
                    return f.read()
        else:
            import os
            if host_in_file and os.path.exists(host_in_file):
                with open(host_in_file, "r", encoding="utf-8") as f:
                    return f.read()
            elif os.path.exists(host_in_file_path):
                with open(host_in_file_path, "r", encoding="utf-8") as f:
                    return f.read()
        return "" 