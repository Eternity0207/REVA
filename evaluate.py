"""Evaluation utilities"""
import time
from datetime import datetime

def measure_time(func):
    """Decorator to measure execution time"""
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        print(f"{func.__name__} took {elapsed:.2f}s")
        return result
    return wrapper

def log_action(action, status="success"):
    """Log an action"""
    timestamp = datetime.now().isoformat()
    print(f"[{timestamp}] {action}: {status}")

if __name__ == "__main__":
    log_action("Test", "OK")
