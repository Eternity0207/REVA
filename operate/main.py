"""
REVA Main Entry Point
Entry point for command-line usage
"""

import argparse
from operate.operate import main as run_agent
from operate.utils.style import ANSI_BRIGHT_MAGENTA, ANSI_RESET


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="REVA - AI Desktop Agent")
    parser.add_argument("-m", "--model", default="fast-gpt", help="Model to use")
    parser.add_argument("--voice", action="store_true", help="Voice mode")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--prompt", type=str, help="Direct objective input")

    try:
        args = parser.parse_args()
        run_agent(
            args.model,
            terminal_prompt=args.prompt,
            voice_mode=args.voice,
            verbose_mode=args.verbose
        )
    except KeyboardInterrupt:
        print(f"\n{ANSI_BRIGHT_MAGENTA}Exiting...{ANSI_RESET}")


if __name__ == "__main__":
    main()
