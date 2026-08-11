def add(a: int, b: int) -> int:
    return a + b


def divide(a: float, b: float) -> float:
    if b == 0:
        raise ValueError("Cannot divide by zero")

    return a / b


def is_even(number: int) -> bool:
    return number % 2 == 0
