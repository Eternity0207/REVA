"""Miscellaneous utilities"""
import os

def convert_percent_to_decimal(value):
    """Convert value to decimal"""
    try:
        return float(value)
    except (ValueError, TypeError):
        return None

def ensure_display():
    """Ensure display is available"""
    if not os.environ.get("DISPLAY"):
        os.environ["DISPLAY"] = ":0"
