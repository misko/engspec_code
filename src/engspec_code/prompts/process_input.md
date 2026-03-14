# Process Input Prompt

You are performing a deep analysis of a codebase using the provided `input.md` context.

## Your Task

Produce TWO outputs:

### Output 1: input_processed.md

A deep analysis document with:

1. **Common Workflows** - Step-by-step breakdown of the main user/developer workflows through the codebase. Trace actual code paths with function names and files.

2. **Common Call Graphs** - The major call paths, written as trees with qualified function names.

3. **Test Coverage Analysis** - For each test file: what module/functions it covers, what properties are verified, what edge cases exist, and what is NOT tested (gaps).

### Output 2: Skeleton .engspec files

One `.engspec` file per source file. Each contains:

- HTML comment metadata (source path, language, hash, status: skeleton)
- For each function:
  - `## \`signature\`` header
  - **Purpose**: Brief description from docstring/analysis
  - **Context**: Called by, Calls, Test coverage status
  - Placeholder sections: Preconditions, Postconditions, Invariants, Implementation Notes, Failure Modes, Test Strategy, Debate Log

## Format

Use the standard .engspec markdown format with `<!-- -->` metadata comments and `###` section headers.
