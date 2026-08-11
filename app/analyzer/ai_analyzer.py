from __future__ import annotations

import json
import os
from typing import Any

from app.models.report import AIAnalysis


class AIAnalyzer:
    """AI-assisted source-code analysis."""

    def __init__(self) -> None:
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = os.getenv(
            "OPENAI_MODEL",
            "gpt-5.5",
        )

    def analyze(self, source: str) -> AIAnalysis:
        """Analyze source code using the configured AI model."""

        if not self.api_key:
            return AIAnalysis(
                error=(
                    "OPENAI_API_KEY is not configured. "
                    "AI analysis was skipped."
                )
            )

        try:
            from openai import OpenAI

            client = OpenAI(api_key=self.api_key)

            prompt = """
You are an expert software verification assistant.

Analyze the following Python program.

Look for:

- logical errors
- boundary-condition problems
- incorrect assumptions
- unsafe operations
- possible runtime failures
- missing edge cases
- suspicious control flow

Do not claim that the program is formally verified.

Return ONLY valid JSON with this structure:

{
  "summary": "short summary",
  "confidence": 0.0,
  "findings": [
    {
      "severity": "INFO|WARNING|ERROR",
      "message": "description",
      "confidence": 0.0
    }
  ],
  "suggested_tests": [
    "description of a useful test"
  ]
}

Python source:

""" + source

            response = client.responses.create(
                model=self.model,
                input=prompt,
            )

            text = response.output_text.strip()
            data: dict[str, Any] = json.loads(text)

            return AIAnalysis(
                summary=str(data.get("summary", "")),
                confidence=_confidence(
                    data.get("confidence")
                ),
                findings=list(
                    data.get("findings", [])
                ),
                suggested_tests=list(
                    data.get("suggested_tests", [])
                ),
            )

        except Exception as exc:
            return AIAnalysis(error=str(exc))


def _confidence(
    value: Any,
) -> float | None:
    """Safely convert confidence to a float."""

    if value is None:
        return None

    try:
        number = float(value)
    except (TypeError, ValueError):
        return None

    return max(
        0.0,
        min(1.0, number),
    )


def ai_analysis_to_issues(
    analysis: AIAnalysis,
) -> list[dict[str, Any]]:
    """Convert AI findings into verification issues."""

    issues = []

    for finding in analysis.findings:
        severity = str(
            finding.get(
                "severity",
                "WARNING",
            )
        ).upper()

        if severity not in {
            "INFO",
            "WARNING",
            "ERROR",
        }:
            severity = "WARNING"

        issues.append(
            {
                "severity": severity,
                "message": str(
                    finding.get(
                        "message",
                        "AI identified a possible issue.",
                    )
                ),
                "confidence": _confidence(
                    finding.get("confidence")
                ),
            }
        )

    return issues
