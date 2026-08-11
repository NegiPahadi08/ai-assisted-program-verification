from pathlib import Path

from app.analyzer.static_analyzer import (
    analyze_file,
)


ROOT = Path(__file__).resolve().parents[1]


def test_correct_example_has_valid_syntax():
    report = analyze_file(
        str(ROOT / "examples" / "correct.py")
    )

    assert report.syntax_valid is True


def test_buggy_example_is_detected():
    report = analyze_file(
        str(ROOT / "examples" / "buggy.py")
    )

    assert report.syntax_valid is True

    messages = [
        issue.message.lower()
        for issue in report.issues
    ]

    assert any(
        "division" in message
        for message in messages
    )

    assert any(
        "eval" in message
        for message in messages
    )


def test_invalid_python_is_rejected(tmp_path):
    source = tmp_path / "invalid.py"

    source.write_text(
        "def broken(:\n    pass\n",
        encoding="utf-8",
    )

    report = analyze_file(
        str(source)
    )

    assert report.syntax_valid is False
    assert report.status == "FAILED"
