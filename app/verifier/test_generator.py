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

    return None


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

    The generator intentionally uses simple boundary
    values rather than pretending that automatically
    generated inputs constitute formal proof.
    """

    tests: list[TestCase] = []

    functions = discover_functions(filename)

    for function_name, _, arguments in functions:
        if not arguments:
            tests.append(
                TestCase(
                    function=function_name,
                    arguments=[],
                    description="Call function with no arguments.",
                )
            )
            continue

        candidates = []

        candidates.append(
            [0] * len(arguments)
        )

        candidates.append(
            [1] * len(arguments)
        )

        candidates.append(
            [-1] * len(arguments)
        )

        typed_values = [
            _value_for_annotation(
                argument.annotation
            )
            for argument in arguments
        ]

        if all(
            value is not None
            for value in typed_values
        ):
            candidates.append(typed_values)

        if len(arguments) == 2:
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
