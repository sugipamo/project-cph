class TestResultFormatter:
    def __init__(self, result):
        self.result = result

    @staticmethod
    def color_text(text, color):
        colors = {
            "red": "\033[31m",
            "green": "\033[32m",
            "yellow": "\033[33m",
            "reset": "\033[0m"
        }
        return f"{colors.get(color, '')}{text}{colors['reset']}"

    def format(self):
        parts = [
            self._format_header(),
            "-" * 17,
            self._format_input(),
            "-" * 17,
            self._format_table(),
            self._format_input_error_bar(),
            self._format_error(),
        ]
        return "\n".join([p for p in parts if p])

    def _format_header(self):
        r = self.result
        name = r["name"]
        returncode, _, _ = r["result"]
        time_sec = r["time"]
        expected = r["expected"]
        stdout = r["result"][1]
        if returncode != 0:
            verdict_colored = self.color_text("RE", "yellow")
        elif stdout.strip() == expected.strip():
            verdict_colored = self.color_text("AC", "green")
        else:
            verdict_colored = self.color_text("WA", "red")
        return f"{name}  {verdict_colored}  {time_sec:.3f}秒"

    def _format_input(self):
        r = self.result
        in_file = r.get("in_file") if "in_file" in r else None
        if in_file and os.path.exists(in_file):
            with open(in_file, "r", encoding="utf-8") as f:
                input_content = f.read().rstrip()
            return input_content
        return ""

    def _format_input_error_bar(self):
        r = self.result
        stderr = r["result"][2]
        if stderr:
            return "-" * 17
        return ""

    def _format_error(self):
        r = self.result
        stderr = r["result"][2]
        if stderr:
            return f"{stderr.strip()}"
        return ""

    def _format_table(self):
        r = self.result
        expected = r["expected"]
        stdout = r["result"][1]
        exp_lines = expected.strip().splitlines()
        out_lines = stdout.strip().splitlines()
        max_exp = max([len(s) for s in exp_lines] + [8]) if exp_lines else 8  # 'Expected'の長さ
        max_out = max([len(s) for s in out_lines] + [6]) if out_lines else 6  # 'Output'の長さ
        max_len = max(len(exp_lines), len(out_lines))
        if max_len == 0:
            return ""
        lines = []
        # カラム名を追加
        lines.append(f"{'Expected':<{max_exp}} | {'Output':<{max_out}}")
        for i in range(max_len):
            exp = exp_lines[i] if i < len(exp_lines) else ""
            out = out_lines[i] if i < len(out_lines) else ""
            lines.append(f"{exp:<{max_exp}} | {out:<{max_out}}")
        return "\n".join(lines) 