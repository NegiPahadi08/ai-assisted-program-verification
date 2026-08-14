from __future__ import annotations

import ast
from typing import Any

from app.models.report import TestCase


def _value_for_annotation(
    annotation: ast.AST | None,
) -> Any:
    """
    Generate a simple example value based on
    a function argument's type annotation.
    """

    if isinstance(annotation, ast.Name):
        if annotation.id == "int":
            return 1

        if annotation.id == "float":
            return 1.0

        if annotation.id == "str":
            return "test"

        if annotation.id == "bool":
            return True

    if isinstance(annotation, ast.Subscript):
        if isinstance(annotation.value, ast.Name):
            if annotation.value.id == "list":
                return [1, 2, 3]

            if annotation.value.id == "set":
                return {1, 2, 3}

    return None

def _value_for_unannotated_argument(
    argument: ast.arg,
    position: int,
) -> Any:
    """
    Generate a conservative example value for an
    unannotated function argument.

    The generator uses the argument name as a small
    hint about the likely value type.
    """

    name = argument.arg.lower()

    if name in {
        "items",
        "values",
        "numbers",
        "numbers_list",
        "lst",
        "list",
    }:
        return [1, 2, 3]

    if name in {
        "target",
        "value",
        "item",
        "needle",
    }:
        return 2

    if name in {
        "code",
        "source",
        "expression",
        "expr",
    }:
        return "1 + 1"

    if name in {
        "a",
        "b",
        "x",
        "y",
        "n",
        "number",
    }:
        return 1

    # Conservative fallback for unknown parameters.
    return 1


def discover_functions(
    filename: str,
) -> list[tuple[str, int, list[ast.arg]]]:
    """
    Find functions defined in a Python source file.
    """

    with open(
        filename,
        "r",
        encoding="utf-8",
    ) as file:
        source = file.read()

    tree = ast.parse(
        source,
        filename=filename,
    )

    functions = []

    for node in ast.walk(tree):
        if isinstance(
            node,
            (
                ast.FunctionDef,
                ast.AsyncFunctionDef,
            ),
        ):
            arguments = [
                *node.args.posonlyargs,
                *node.args.args,
                *node.args.kwonlyargs,
            ]

            functions.append(
                (
                    node.name,
                    node.lineno,
                    arguments,
                )
            )

    return functions


def generate_tests(
    filename: str,
    limit: int = 8,
) -> list[TestCase]:
    """
    Generate conservative candidate test cases.

    The generator uses simple boundary values and
    values derived from type annotations.
    """

    tests: list[TestCase] = []

    functions = discover_functions(filename)

    for function_name, _, arguments in functions:

        if not arguments:
            tests.append(
                TestCase(
                    function=function_name,
                    arguments=[],
                    description=(
                        "Call function with no arguments."
                    ),
                )
            )

            if len(tests) >= limit:
                return tests

            continue

        candidates = []

        # Generate values based on type annotations.
        # Generate values based on type annotations.
        typed_values = [
            (
                _value_for_annotation(argument.annotation)
                if argument.annotation is not None
                else _value_for_unannotated_argument(
                    argument,
                    position,
                )
            )
            for position, argument in enumerate(arguments)
        ]

        if all(
            value is not None
            for value in typed_values
        ):
            candidates.append(typed_values)

            
        # Special handling for list arguments.
        if len(arguments) == 1:
            annotation = arguments[0].annotation

            if isinstance(annotation, ast.Subscript):
                if isinstance(annotation.value, ast.Name):
                    if annotation.value.id == "list":
                        candidates.append([[]])
                        candidates.append([[0]])
                        candidates.append([[1, 2, 3]])
                        candidates.append([[-1, 1]])

        # Generic numeric boundary values.
        if all(
            isinstance(argument.annotation, ast.Name)
            and argument.annotation.id in {
                "int",
                "float",
            }
            for argument in arguments
        ):
            candidates.append(
                [0] * len(arguments)
            )

            candidates.append(
                [1] * len(arguments)
            )

            candidates.append(
                [-1] * len(arguments)
            )

        # Explicit zero-denominator tests.
        if len(arguments) == 2:
            second_annotation = arguments[1].annotation

            if isinstance(second_annotation, ast.Name):
                if second_annotation.id in {
                    "int",
                    "float",
                }:
                    candidates.append([1, 0])
                    candidates.append([0, 1])

        seen = set()

        for candidate in candidates:
            key = repr(candidate)

            if key in seen:
                continue

            seen.add(key)

            tests.append(
                TestCase(
                    function=function_name,
                    arguments=candidate,
                    description=(
                        f"Generated candidate for "
                        f"{function_name}"
                    ),
                )
            )

            if len(tests) >= limit:
                return tests

    return tests