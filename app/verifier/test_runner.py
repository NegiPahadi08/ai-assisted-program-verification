from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

from app.models.report import (
    TestCase,
    TestExecution,
)


def run_test_case(
    filename: str,
    test_case: TestCase,
    timeout: float = 3.0,
) -> TestExecution:
    """
    Execute one generated test in a separate
    Python process.

    The timeout prevents normal infinite loops
    from blocking the main verification process.

    NOTE:
    This is NOT a security sandbox.
    """

    source = Path(filename).resolve()

    arguments = json.dumps(
        test_case.arguments
    )

    script = f"""
import importlib.util
import json

spec = importlib.util.spec_from_file_location(
    "target",
    {str(source)!r}
)

module = importlib.util.module_from_spec(
    spec
)

spec.loader.exec_module(module)

function = getattr(
    module,
    {test_case.function!r}
)

arguments = json.loads(
    {arguments!r}
)

result = function(*arguments)

print(
    json.dumps(
        {{
            "ok": True,
            "result": result
        }},
        default=repr
    )
)
"""

    start = time.perf_counter()

    try:
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                script,
            ],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(source.parent),
        )

        duration = (
            time.perf_counter() - start
        ) * 1000

        if result.returncode == 0:
            return TestExecution(
                test=test_case,
                passed=True,
                output=result.stdout.strip(),
                error=result.stderr.strip(),
                duration_ms=duration,
            )

        return TestExecution(
            test=test_case,
            passed=False,
            output=result.stdout.strip(),
            error=(
                result.stderr.strip()
                or
                f"Process exited with "
                f"code {result.returncode}."
            ),
            duration_ms=duration,
        )

    except subprocess.TimeoutExpired:
        duration = (
            time.perf_counter() - start
        ) * 1000

        return TestExecution(
            test=test_case,
            passed=False,
            error="Execution timed out.",
            duration_ms=duration,
        )

    except Exception as exc:
        duration = (
            time.perf_counter() - start
        ) * 1000

        return TestExecution(
            test=test_case,
            passed=False,
            error=str(exc),
            duration_ms=duration,
        )
