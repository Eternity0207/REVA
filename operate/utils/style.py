ANSI_GREEN = "\033[92m"
ANSI_RED = "\033[91m"
ANSI_YELLOW = "\033[93m"
ANSI_BLUE = "\033[94m"
ANSI_BRIGHT_MAGENTA = "\033[95m"
ANSI_RESET = "\033[0m"

from prompt_toolkit.styles import Style

style = Style.from_dict({"prompt": "blue bold"})

def colored(text, color):
    return f"{color}{text}{ANSI_RESET}"

def bold(text):
    return f"\033[1m{text}{ANSI_RESET}"
