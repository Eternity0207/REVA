"""Miscellaneous utilities"""

def convert_percent_to_decimal(value):
    """Convert value to decimal"""
    try:
        return float(value)
    except (ValueError, TypeError):
        return None
