"""CLI entry point"""
import sys
import argparse
from operate.operate import main

def cli():
    parser = argparse.ArgumentParser(description="REVA - AI OS Agent")
    parser.add_argument("command", nargs="?", help="Command to execute")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("-m", "--model", default="fast-gpt", help="Model to use")
    args = parser.parse_args()

    main(model=args.model, terminal_prompt=args.command, verbose_mode=args.verbose)

if __name__ == "__main__":
    cli()
