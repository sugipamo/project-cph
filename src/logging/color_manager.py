ANSI_CODES = {
    "red": "\033[31m",
    "green": "\033[32m",
    "yellow": "\033[33m",
    "blue": "\033[34m",
    "magenta": "\033[35m",
    "cyan": "\033[36m",
    "white": "\033[37m",
    "gray": "\033[90m",
}
RESET_CODE = "\033[0m"

def to_ansi(color: str) -> str:
    if color in ANSI_CODES:
        return ANSI_CODES[color]
    if color and color.startswith("\033[") and color.endswith("m"):
        return color
    raise ValueError(f"未対応の色: {color}")

def apply_color(text: str, color: str) -> str:
    code = to_ansi(color)
    return f"{code}{text}{RESET_CODE}"
