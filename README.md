# AI-Assisted Program Verification

AI-Assisted Program Verification is a software verification framework that combines:

- Static program analysis
- Automated test generation
- Program execution
- AI-assisted code analysis
- Verification reporting

The goal is to use Artificial Intelligence as an assistant while relying on deterministic analysis and executable tests as independent evidence.

## Project Goal

Traditional program verification can be difficult and time-consuming.

This project explores how Artificial Intelligence can assist developers and researchers by:

1. Understanding source code
2. Detecting possible defects
3. Generating test cases
4. Executing generated tests
5. Identifying edge cases
6. Producing an evidence-based verification report

AI does not make the final verification decision by itself.

## Architecture

```text
                    SOURCE CODE
                         |
          +--------------+--------------+
          |              |              |
          v              v              v
    Static Analysis   AI Analysis   Test Generation
          |              |              |
          |              |              v
          |              |         Test Execution
          |              |              |
          +--------------+--------------+
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
         VERIFIED     PARTIAL      FAILED
