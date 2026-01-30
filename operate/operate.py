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
    print(f"{ANSI_BRIGHT_MAGENTA}Model:{ANSI_RESET} Groq ({model})")
    print("-" * 40)

    objective = terminal_prompt or input(f"{USER_QUESTION}\n> ")

    if config.verbose:
        logger.info(f"Objective: {objective}")

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
            [operations, messages], session_id = asyncio.run(
                get_next_action(model, messages, objective, session_id)
            )

            if operate(operations, model):
                break

        except ModelNotRecognizedException as e:
            print(f"{ANSI_RED}Model error: {e}{ANSI_RESET}")
            break
        except Exception as e:
            print(f"{ANSI_RED}Error: {e}{ANSI_RESET}")
            if config.verbose:
                logger.exception(e)
            break

    print(f"\n{ANSI_GREEN}[REVA]{ANSI_RESET} Session complete")

def operate(operations, model):
    logger.info(f"Executing {len(operations)} operations")

    for op in operations:
        time.sleep(1)
        op_type = op.get("operation", "").lower()
        thought = op.get("thought", "")

        if op_type == "press":
            keys = op.get("keys", [])
            operating_system.press(keys)
            print(f"  {ANSI_BLUE}Press:{ANSI_RESET} {keys}")

        elif op_type == "write":
            content = op.get("content", "")
            operating_system.write(content)
            print(f"  {ANSI_BLUE}Type:{ANSI_RESET} {content[:50]}...")

        elif op_type == "click":
            x, y = op.get("x"), op.get("y")
            operating_system.mouse({"x": x, "y": y})
            print(f"  {ANSI_BLUE}Click:{ANSI_RESET} ({x}, {y})")

        elif op_type == "scroll":
            operating_system.scroll()
            print(f"  {ANSI_BLUE}Scroll{ANSI_RESET}")

        elif op_type == "done":
            summary = op.get("summary", "Complete")
            print(f"\n{ANSI_GREEN}Complete:{ANSI_RESET} {summary}")
            return True

        else:
            print(f"  {ANSI_RED}Unknown:{ANSI_RESET} {op_type}")
            return True

        if thought and config.verbose:
            print(f"    Thought: {thought}")

    return False
