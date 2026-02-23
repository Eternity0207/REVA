"""Code complexity checker"""
import ast
import sys

def analyze_file(filepath):
    """Analyze Python file for complexity"""
    with open(filepath) as f:
        tree = ast.parse(f.read())

    functions = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]

    print(f"File: {filepath}")
    print(f"Functions: {len(functions)}")
    for func in functions:
        print(f"  - {func.name}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        analyze_file(sys.argv[1])
