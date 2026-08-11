def divide(a, b):
    return a / b


def calculate_average(numbers):
    total = sum(numbers)
    return total / len(numbers)


def unsafe_execute(code):
    return eval(code)


def find_value(items, target):
    for item in items:
        if item == target:
            return item

    return missing_value
