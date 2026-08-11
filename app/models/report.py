from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class Issue:
    """
    Represents a problem discovered during verification.
    """

    severity: str
    message: str
    line: int | None = None
    source: str = "static"
    confidence: float | None = None


@dataclass
class TestCase:
    """
    Represents one automatically generated test case.
    """

    function: str
    arguments: list[Any]
    expected: Any | None = None
    description: str = ""


@dataclass
class TestExecution:
    """
    Stores the result of executing a generated test.
    """

    test: TestCase
    passed: bool
    output: str = ""
    error: str = ""
    duration_ms: float = 0.0


@dataclass
class AIAnalysis:
    """
    Stores the result returned by the AI analyzer.
    """

    summary: str = ""

    findings: list[dict[str, Any]] = field(
        default_factory=list
    )

    suggested_tests: list[str] = field(
        default_factory=list
    )

    confidence: float | None = None

    error: str | None = None


@dataclass
class VerificationReport:
    """
    Complete verification report for a source file.
    """

    file: str

    syntax_valid: bool = False

    issues: list[Issue] = field(
        default_factory=list
    )

    generated_tests: list[TestCase] = field(
        default_factory=list
    )

    executions: list[TestExecution] = field(
        default_factory=list
    )

    ai: AIAnalysis | None = None

    status: str = "NOT VERIFIED"

    @property
    def tests_passed(self) -> int:
        """
        Return the number of successful tests.
        """

        return sum(
            execution.passed
            for execution in self.executions
        )

    @property
    def tests_failed(self) -> int:
        """
        Return the number of failed tests.
        """

        return sum(
            not execution.passed
            for execution in self.executions
        )

    def add_issue(
        self,
        severity: str,
        message: str,
        line: int | None = None,
        source: str = "static",
        confidence: float | None = None,
    ) -> None:
        """
        Add a verification finding to the report.
        """

        self.issues.append(
            Issue(
                severity=severity,
                message=message,
                line=line,
                source=source,
                confidence=confidence,
            )
        )

    def calculate_status(self) -> str:
        """
        Calculate the overall verification status.
        """

        # Invalid Python source cannot be verified.
        if not self.syntax_valid:
            self.status = "FAILED"
            return self.status

        # A hard error or failed executable test means
        # the program is not fully verified.
        hard_errors = any(
            issue.severity == "ERROR"
            for issue in self.issues
        )

        if hard_errors or self.tests_failed:
            self.status = "PARTIALLY VERIFIED"

        elif self.issues:
            self.status = "PARTIALLY VERIFIED"

        else:
            self.status = "VERIFIED"

        return self.status

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the complete report into a dictionary.
        """

        data = asdict(self)

        data["tests_passed"] = self.tests_passed
        data["tests_failed"] = self.tests_failed

        return data
