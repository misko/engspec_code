"""
A simple Python module for testing engspec generation.
"""


def add(a: int, b: int) -> int:
    """Add two integers."""
    return a + b


def divide(a: float, b: float) -> float:
    """Divide a by b."""
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b


class Calculator:
    """A simple calculator."""

    def __init__(self) -> None:
        self.history: list[float] = []

    def compute(self, op: str, a: float, b: float) -> float:
        """Compute an operation and record it."""
        if op == "add":
            result = a + b
        elif op == "div":
            result = divide(a, b)
        else:
            raise ValueError(f"Unknown operation: {op}")
        self.history.append(result)
        return result
