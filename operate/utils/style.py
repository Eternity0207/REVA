"""Terminal styling"""
from prompt_toolkit.styles import Style

ANSI_GREEN = "\033[92m"
ANSI_RED = "\033[91m"
ANSI_YELLOW = "\033[93m"
ANSI_BLUE = "\033[94m"
ANSI_BRIGHT_MAGENTA = "\033[95m"
ANSI_RESET = "\033[0m"

style = Style.from_dict({"prompt": "blue bold"})
