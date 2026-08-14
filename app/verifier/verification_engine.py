from __future__ import annotations

import ast
import builtins
from typing import Any

from app.analyzer.ai_analyzer import (
    AIAnalyzer,
    ai_analysis_to_issues,
)
from app.models.report import TestCase, VerificationReport
from app.verifier.test_generator import generate_tests
from app.verifier.test_runner import run_test_case


def _function_has_expected_exception(
    filename: str,
    function_name: str,
    exception_name: str,
) -> bool:
    """
    Check whether a function explicitly raises the
    exception encountered during generated testing.

    This allows intentional input validation such as:

        if b == 0:
            raise ValueError(...)
    """

    try:
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

    except (OSError, SyntaxError):
        return False

    for node in ast.walk(tree):
        if not isinstance(
            node,
            (
                ast.FunctionDef,
                ast.AsyncFunctionDef,
            ),
        ):
            continue

        if node.name != function_name:
            continue

        for child in ast.walk(node):
            if not isinstance(child, ast.Raise):
                continue

            if child.exc is None:
                continue

            exception = child.exc

            if isinstance(exception, ast.Call):
                exception = exception.func

            if isinstance(exception, ast.Name):
                if exception.id == exception_name:
                    return True

            if isinstance(exception, ast.Attribute):
                if exception.attr == exception_name:
                    return True

    return False


def _is_expected_exception(
    filename: str,
    test_case: TestCase,
    error: str,
) -> bool:
    """
    Determine whether a failed execution represents
    intentional exception handling.

    Example:

        divide(0, 0)

    may intentionally raise ValueError because the
    function rejects a zero denominator.
    """

    if not error:
        return False

    known_exceptions = [
        "ValueError",
        "TypeError",
        "KeyError",
        "IndexError",
        "ZeroDivisionError",
    ]

    for exception_name in known_exceptions:
        if exception_name in error:
            return _function_has_expected_exception(
                filename,
                test_case.function,
                exception_name,
            )

    return False

def _find_undefined_names(
    filename: str,
) -> list[tuple[str, int]]:
    """
    Find names that are read but never defined in the source.

    Returns:
        A list of (name, line_number) pairs.
    """

    try:
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

    except (OSError, SyntaxError):
        return []

    defined: set[str] = set()
    loaded: list[tuple[str, int]] = []

    builtin_names = set(dir(builtins))
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            if isinstance(node.ctx, ast.Store):
                defined.add(node.id)

            elif isinstance(node.ctx, ast.Load):
                loaded.append(
                    (node.id, node.lineno)
                )

        elif isinstance(node, ast.FunctionDef):
            defined.add(node.name)

            for argument in (
                *node.args.posonlyargs,
                *node.args.args,
                *node.args.kwonlyargs,
            ):
                defined.add(argument.arg)

        elif isinstance(node, ast.AsyncFunctionDef):
            defined.add(node.name)

            for argument in (
                *node.args.posonlyargs,
                *node.args.args,
                *node.args.kwonlyargs,
            ):
                defined.add(argument.arg)

        elif isinstance(node, ast.ClassDef):
            defined.add(node.name)

        elif isinstance(node, ast.Import):
            for alias in node.names:
                defined.add(
                    alias.asname
                    or alias.name.split(".")[0]
                )

        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                if alias.name != "*":
                    defined.add(
                        alias.asname or alias.name
                    )

    undefined = []

    for name, line in loaded:
        if name in defined:
            continue

        if name in builtin_names:
            continue

        undefined.append(
            (name, line)
        )

    return undefined

def verify_program(
    filename: str,
    enable_ai: bool = False,
    test_limit: int = 8,
) -> VerificationReport:
    """
    Verify a Python program using syntax checking
    and automatically generated executable tests.
    """

    report = VerificationReport(
        file=filename
    )

    # 2. Static undefined-name analysis
    undefined_names = _find_undefined_names(
        filename
    )

    for name, line in undefined_names:
        report.add_issue(
            severity="ERROR",
            message=(
                f"Undefined variable '{name}'."
            ),
            line=line,
            source="static",
        )

   
    # 1. Check Python syntax
    try:
        with open(
            filename,
            "r",
            encoding="utf-8",
        ) as file:
            source = file.read()

        ast.parse(
            source,
            filename=filename,
        )

        report.syntax_valid = True

    except SyntaxError as exc:
        report.syntax_valid = False

        report.add_issue(
            severity="ERROR",
            message=f"Syntax error: {exc.msg}",
            line=exc.lineno,
            source="static",
        )

        report.calculate_status()
        return report

    except OSError as exc:
        report.syntax_valid = False

        report.add_issue(
            severity="ERROR",
            message=f"Unable to read source file: {exc}",
            source="static",
        )

        report.calculate_status()
        return report

    # 2. Generate tests
    try:
        report.generated_tests = generate_tests(
            filename,
            limit=test_limit,
        )

    except Exception as exc:
        report.add_issue(
            severity="ERROR",
            message=f"Test generation failed: {exc}",
            source="generator",
        )

        report.calculate_status()
        return report

    # 3. Run generated tests
    for test_case in report.generated_tests:

        execution = run_test_case(
            filename,
            test_case,
        )

        # Intentional exception handling is considered
        # successful behavior rather than a failed test.
        if not execution.passed:
            error_message = (
                execution.error
                or "Generated test failed."
            )

            if _is_expected_exception(
                filename,
                test_case,
                error_message,
            ):
                execution.passed = True
                execution.error = (
                    "Expected exception raised."
                )

        report.executions.append(
            execution
        )

        if not execution.passed:
            error_message = (
                execution.error
                or "Generated test failed."
            )

            report.add_issue(
                severity="ERROR",
                message=(
                    f"Test failed for "
                    f"{test_case.function}"
                    f"{tuple(test_case.arguments)}: "
                    f"{error_message}"
                ),
                source="dynamic",
            )

    # AI is optional for now.
    # 4. AI-assisted analysis
    if enable_ai:
        try:
            analyzer = AIAnalyzer()

            analysis = analyzer.analyze(
                source
            )

            report.ai = analysis

            for issue in ai_analysis_to_issues(
                analysis
            ):
                report.add_issue(
                    severity=issue["severity"],
                    message=issue["message"],
                    source="ai",
                    confidence=issue["confidence"],
                )

        except Exception as exc:
            report.add_issue(
                severity="WARNING",
                message=f"AI analysis failed: {exc}",
                source="ai",
            )

    # 5. Calculate final status
    report.calculate_status()

    return report