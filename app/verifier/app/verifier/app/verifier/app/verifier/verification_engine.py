from __future__ import annotations

import os

from app.analyzer.ai_analyzer import (
    AIAnalyzer,
    ai_analysis_to_issues,
)

from app.analyzer.static_analyzer import (
    analyze_file,
)

from app.models.report import (
    VerificationReport,
)

from app.verifier.test_generator import (
    generate_tests,
)

from app.verifier.test_runner import (
    run_test_case,
)


def verify_program(
    filename: str,
    enable_ai: bool = False,
    timeout: float = 3.0,
    generate: bool = True,
) -> VerificationReport:
    """
    Run the complete verification pipeline.

    Pipeline:

        Source Code
             |
             v
        Static Analysis
             |
             v
        Test Generation
             |
             v
        Test Execution
             |
             v
        Optional AI Analysis
             |
             v
        Verification Report
    """

    # -------------------------------------------------
    # 1. Static analysis
    # -------------------------------------------------

    report = analyze_file(
        filename
    )

    # If syntax is invalid, stop here.
    if not report.syntax_valid:
        return report

    # -------------------------------------------------
    # 2. Automatic test generation
    # -------------------------------------------------

    if generate:

        report.generated_tests = (
            generate_tests(filename)
        )

        # -------------------------------------------------
        # 3. Execute generated tests
        # -------------------------------------------------

        for test in report.generated_tests:

            execution = run_test_case(
                filename,
                test,
                timeout=timeout,
            )

            report.executions.append(
                execution
            )

            if not execution.passed:

                report.add_issue(
                    severity="ERROR",
                    message=(
                        "Generated test failed for "
                        f"{test.function}"
                        "("
                        f"{', '.join(map(repr, test.arguments))}"
                        "): "
                        f"{execution.error}"
                    ),
                    source="execution",
                )

    # -------------------------------------------------
    # 4. Optional AI analysis
    # -------------------------------------------------

    if enable_ai:

        try:

            with open(
                filename,
                "r",
                encoding="utf-8",
            ) as file:

                source = file.read()

            report.ai = AIAnalyzer().analyze(
                source
            )

            # Add AI findings to the main report.
            for issue in ai_analysis_to_issues(
                report.ai
            ):

                report.add_issue(
                    severity=issue["severity"],
                    message=issue["message"],
                    source="ai",
                    confidence=issue[
                        "confidence"
                    ],
                )

        except Exception as exc:

            report.add_issue(
                severity="WARNING",
                message=(
                    f"AI integration error: {exc}"
                ),
                source="ai",
            )

    # -------------------------------------------------
    # 5. Calculate final result
    # -------------------------------------------------

    report.calculate_status()

    return report
