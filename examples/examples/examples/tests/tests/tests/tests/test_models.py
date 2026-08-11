from app.models.report import (
    AIAnalysis,
    TestCase,
    TestExecution,
    VerificationReport,
)


def test_verification_report_serialization():
    test = TestCase(
        function="add",
        arguments=[1, 2],
        description="Basic addition",
    )

    execution = TestExecution(
        test=test,
        passed=True,
        output="3",
    )

    report = VerificationReport(
        file="example.py",
        syntax_valid=True,
    )

    report.generated_tests.append(test)
    report.executions.append(execution)

    report.calculate_status()

    data = report.to_dict()

    assert data["file"] == "example.py"
    assert data["syntax_valid"] is True
    assert data["tests_passed"] == 1
    assert data["tests_failed"] == 0
    assert data["status"] == "VERIFIED"


def test_ai_analysis_without_key():
    analysis = AIAnalysis(
        error="API key not configured"
    )

    assert analysis.error is not None
