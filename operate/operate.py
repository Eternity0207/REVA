"""Main agent loop"""
import sys
import os
import time
import asyncio
import platform
from loguru import logger
from operate.config import Config
from operate.exceptions import ModelNotRecognizedException
from operate.models.prompts import USER_QUESTION, get_system_prompt
from operate.utils.style import ANSI_GREEN, ANSI_RED, ANSI_BLUE, ANSI_RESET, ANSI_BRIGHT_MAGENTA
from operate.utils.operating_system import OperatingSystem
from operate.models.apis import get_next_action

config = Config()
operating_system = OperatingSystem()

def main(model, terminal_prompt=None, voice_mode=False, verbose_mode=False):
    config.verbose = verbose_mode

    if config.validation(model, voice_mode):
        print(f"{ANSI_RED}Error: API key not configured{ANSI_RESET}")
        return

    print(f"\n{ANSI_GREEN}[REVA]{ANSI_RESET} AI OS Controller")
    print(f"{ANSI_BRIGHT_MAGENTA}Model:{ANSI_RESET} Groq")
    print("-" * 40)

    objective = terminal_prompt or input(f"{USER_QUESTION}\n> ")

    if not objective.strip():
        print(f"{ANSI_RED}No objective provided{ANSI_RESET}")
        return

    system_prompt = get_system_prompt(model, objective)
    messages = [{"role": "system", "content": system_prompt}]

    session_id = None
    loop_count = 0
    max_loops = 30

    while loop_count < max_loops:
        time.sleep(2)
        loop_count += 1

        if config.verbose:
            print(f"\n{ANSI_BLUE}[Loop {loop_count}/{max_loops}]{ANSI_RESET}")

        try:
            result, session_id = asyncio.run(
                get_next_action(model, messages, objective, session_id)
            )

            if not result or len(result) < 2:
                logger.warning("Invalid API response")
                continue

            operations, messages = result

            if not operations:
                logger.warning("Empty operations")
                continue

            if operate(operations, model):
                break

        except Exception as e:
            print(f"{ANSI_RED}Error: {e}{ANSI_RESET}")
            break

    print(f"\n{ANSI_GREEN}[REVA]{ANSI_RESET} Done")

def operate(operations, model):
    if not operations:
        return False

    for op in operations:
        time.sleep(1)
        op_type = op.get("operation", "").lower()

        if op_type == "press":
            operating_system.press(op.get("keys", []))
            print(f"  {ANSI_BLUE}Press:{ANSI_RESET} {op.get('keys')}")
        elif op_type == "write":
            operating_system.write(op.get("content", ""))
            print(f"  {ANSI_BLUE}Type:{ANSI_RESET} {op.get('content', '')[:40]}")
        elif op_type == "click":
            operating_system.mouse({"x": op.get("x"), "y": op.get("y")})
            print(f"  {ANSI_BLUE}Click:{ANSI_RESET} ({op.get('x')}, {op.get('y')})")
        elif op_type == "scroll":
            operating_system.scroll()
            print(f"  {ANSI_BLUE}Scroll{ANSI_RESET}")
        elif op_type == "done":
            print(f"\n{ANSI_GREEN}Done:{ANSI_RESET} {op.get('summary')}")
            return True
        else:
            print(f"  {ANSI_RED}Unknown:{ANSI_RESET} {op_type}")

    return False
