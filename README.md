# AI-Assisted Program Verification

A Python-based program verification framework that combines static program analysis, automated test generation, test execution, and AI-assisted code analysis to produce evidence-based verification results.

The goal is to help developers identify potential defects and evaluate program behavior using multiple sources of evidence rather than relying on AI alone.

---

## Project Overview

Software verification can be difficult and time-consuming, especially when programs contain hidden defects or edge cases.

This project provides an automated verification pipeline that:

1. Analyzes Python source code for potential problems
2. Detects static issues such as undefined variables
3. Generates candidate test cases automatically
4. Executes generated tests
5. Collects execution results
6. Uses AI-assisted analysis when available
7. Combines the evidence into a verification result

The system does not allow AI to make the final verification decision by itself. Static analysis and executable tests provide independent evidence.

---

## Features

### Static Program Analysis

- Detects potential source-code problems
- Reports issues with severity and source information
- Identifies problems such as undefined variables

### Automated Test Generation

- Generates candidate test cases for program functions
- Includes normal and edge-case inputs

### Test Execution

- Executes generated tests
- Records output and errors
- Records pass/fail status
- Records execution time

### AI-Assisted Analysis

- Integrates with the OpenAI API
- Provides additional code-analysis assistance when API access is available
- Keeps AI analysis separate from deterministic verification evidence

### Evidence-Based Verification

The verification engine combines available evidence and produces one of:

- `VERIFIED`
- `PARTIALLY VERIFIED`
- `FAILED`

### Automated Testing

The project uses pytest for automated testing.

---

## Architecture

```text
                         SOURCE CODE
                              |
             +----------------+----------------+
             |                |                |
             v                v                v
      Static Analysis    AI Analysis    Test Generation
             |                |                |
             |                |                v
             |                |         Test Execution
             |                |                |
             +----------------+----------------+
                              |
                              v
                    Verification Engine
                              |
                              v
                    Verification Report
                              |
                  +-----------+-----------+
                  |           |           |
                  v           v           v
              VERIFIED    PARTIAL     FAILED