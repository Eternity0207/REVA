"""Terminal styling"""
from prompt_toolkit.styles import Style

ANSI_GREEN = "\033[92m"
ANSI_RED = "\033[91m"
ANSI_YELLOW = "\033[93m"
ANSI_BLUE = "\033[94m"
ANSI_BRIGHT_MAGENTA = "\033[95m"
ANSI_RESET = "\033[0m"

style = Style.from_dict({"prompt": "blue bold"})

def green(text): return f"{ANSI_GREEN}{text}{ANSI_RESET}"
def red(text): return f"{ANSI_RED}{text}{ANSI_RESET}"
def blue(text): return f"{ANSI_BLUE}{text}{ANSI_RESET}"
def yellow(text): return f"{ANSI_YELLOW}{text}{ANSI_RESET}"

def print_banner():
    print(f"\n{ANSI_BRIGHT_MAGENTA}╔═══════════════════════════════╗{ANSI_RESET}")
    print(f"{ANSI_BRIGHT_MAGENTA}║         REVA v2.0             ║{ANSI_RESET}")
    print(f"{ANSI_BRIGHT_MAGENTA}║   AI OS Controlling Agent     ║{ANSI_RESET}")
    print(f"{ANSI_BRIGHT_MAGENTA}╚═══════════════════════════════╝{ANSI_RESET}\n")
