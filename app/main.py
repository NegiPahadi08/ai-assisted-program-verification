from __future__ import annotations

import argparse
import json
import sys

from dotenv import load_dotenv

from app.verifier.verification_engine import verify_program


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="aipv",
        description="AI-Assisted Program Verification",
    )

    parser.add_argument(
        "file",
        help="Python source file to verify",
    )

    parser.add_argument(
        "--ai",
        action="store_true",
        help="Enable AI-assisted analysis",
    )

    parser.add_argument(
        "--json",
        dest="json_path",
        help="Save verification report as JSON",
    )

    parser.add_argument(
        "--timeout",
        type=float,
        default=3.0,
        help="Timeout in seconds for each generated test",
    )

    parser.add_argument(
        "--no-tests",
        action="store_true",
        help="Skip automatically generated tests",
    )

    return parser


def print_report(report) -> None:
    print("=" * 60)
    print(" AI-ASSISTED PROGRAM VERIFICATION")
    print("=" * 60)

    print(f"File: {report.file}")

    print("\nSyntax:")

    if report.syntax_valid:
        print("  ✓ Valid")
    else:
        print("  ✗ Invalid")

    print("\nFindings:")

    if not report.issues:
        print("  ✓ No findings")
    else:
        for issue in report.issues:
            location = ""

            if issue.line:
                location = f" (line {issue.line})"

            confidence = ""

            if issue.confidence is not None:
                confidence = f" [confidence={issue.confidence:.2f}]"

            print(
                f"  {issue.severity:<7} "
                f"{issue.message}"
                f"{location}"
                f"{confidence}"
            )

    print("\nGenerated Tests:")
    print(f"  Candidates: {len(report.generated_tests)}")
    print(f"  Passed:     {report.tests_passed}")
    print(f"  Failed:     {report.tests_failed}")

    if report.ai:
        print("\nAI Analysis:")

        if report.ai.error:
            print(f"  ! {report.ai.error}")
        else:
            print(f"  Summary: {report.ai.summary}")

            if report.ai.confidence is not None:
                print(
                    f"  Confidence: "
                    f"{report.ai.confidence:.2f}"
                )

    print("\nVerification Result:")
    print(f"  {report.status}")

    print("=" * 60)


def main() -> int:
    load_dotenv()

    parser = build_parser()
    args = parser.parse_args()

    report = verify_program(
        args.file,
        enable_ai=args.ai,
        timeout=args.timeout,
        generate=not args.no_tests,
    )

    print_report(report)

    if args.json_path:
        with open(
            args.json_path,
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                report.to_dict(),
                file,
                indent=2,
                default=str,
            )

        print(
            f"\nJSON report written to: "
            f"{args.json_path}"
        )

    if report.status == "FAILED":
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
