from pathlib import Path

from app.verifier.test_generator import (
    generate_tests,
)

from app.verifier.verification_engine import (
    verify_program,
)


ROOT = Path(__file__).resolve().parents[1]


def test_test_generator_finds_functions():
    tests = generate_tests(
        str(ROOT / "examples" / "correct.py")
    )

    assert len(tests) > 0

    function_names = {
        test.function
        for test in tests
    }

    assert "add" in function_names
    assert "divide" in function_names


def test_correct_program_verification():
    report = verify_program(
        str(ROOT / "examples" / "correct.py"),
        enable_ai=False,
    )

    assert report.syntax_valid is True
    assert len(report.generated_tests) > 0
    assert report.tests_passed > 0


def test_buggy_program_verification():
    report = verify_program(
        str(ROOT / "examples" / "buggy.py"),
        enable_ai=False,
    )

    assert report.syntax_valid is True
    assert report.status == "PARTIALLY VERIFIED"

    assert any(
    issue.source == "static"
    and "missing_value" in issue.message
    for issue in report.issues
)