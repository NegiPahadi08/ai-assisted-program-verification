# System Architecture

## Overview

AI-Assisted Program Verification uses multiple independent components to analyze Python programs.

```text
                         +----------------+
                         |   Python Code  |
                         +-------+--------+
                                 |
                +----------------+----------------+
                |                                 |
                v                                 v
       +------------------+              +------------------+
       | Static Analyzer  |              |   AI Analyzer    |
       |      AST         |              |  Optional LLM    |
       +--------+---------+              +--------+---------+
                |                                 |
                +----------------+----------------+
                                 |
                                 v
                      +---------------------+
                      |   Test Generator    |
                      +----------+----------+
                                 |
                                 v
                      +---------------------+
                      |    Test Runner      |
                      +----------+----------+
                                 |
                                 v
                      +---------------------+
                      | Verification Engine |
                      +----------+----------+
                                 |
                                 v
                      +---------------------+
                      | Verification Report |
                      +---------------------+
