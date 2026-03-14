# Project: sample

## Description
A simple calculator module for testing engspec generation. Contains basic arithmetic operations (add, divide) and a Calculator class that dispatches operations and keeps history.

## Test Environment Setup
```bash
pip install pytest
```

## Running Tests
```bash
pytest tests/
```

## Examples
```python
from sample import add, divide, Calculator

result = add(1, 2)  # 3
result = divide(10, 3)  # 3.333...

calc = Calculator()
calc.compute("add", 1, 2)  # 3
calc.compute("div", 10, 3)  # 3.333...
print(calc.history)  # [3, 3.333...]
```

## Notes
- Simple test fixture, not a real project
- No external dependencies
- Python 3.10+
