from __future__ import annotations

import argparse
import json

from dotenv import load_dotenv

from app.verifier.verification_engine import verify_program

def main() -> None:
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="AI-Assisted Program Verification"
    )

    parser.add_argument(
        "filename",
        help="Python file to verify",
    )

    parser.add_argument(
        "--ai",
        action="store_true",
        help="Enable AI analysis",
    )

    args = parser.parse_args()

    report = verify_program(
        args.filename,
        enable_ai=args.ai,
    )

    print(
        json.dumps(
            report.to_dict(),
            indent=2,
            default=str,
        )
    )


if __name__ == "__main__":
    main()