# engspec_code

English-first specification layer for any codebase. Every function gets a parallel `.engspec` specification written in structured English, detailed enough that an AI agent can re-implement the function from the spec alone.

## What This Does

`engspec_code` provides three standalone prompts that form a complete pipeline:

```
engspec_prompt.md          →  code → engspec (produces project-engspec.zip)
engspec_tester_prompt.md   →  adversarial debate (produces project-engspec-tested.zip)
engspec_to_code_prompt.md  →  engspec → code (regenerates codebase from specs)
```

No installation required. Each prompt is a self-contained markdown file you give to Claude.

## Quick Start

### 1. Generate specs from a repo

```
Read /path/to/engspec_code/engspec_prompt.md for your instructions.

Please clone https://github.com/encode/httpx, analyze the repo, and produce validated .engspec files for all source files.

No input.md is provided — auto-generate the project context from the repo.
```

### 2. Run adversarial analysis (optional)

```
Read /path/to/engspec_code/engspec_tester_prompt.md for your instructions.

Here is the engspec package at: /path/to/httpx-engspec
Here is the source repo at: /path/to/httpx

Please run adversarial analysis.
```

### 3. Regenerate code from specs

```
Read /path/to/engspec_code/engspec_to_code_prompt.md for your instructions.

Here is the engspec package: /path/to/httpx-engspec.zip

Please regenerate the full codebase into /home/ubuntu/httpx-regen/ and run tests.
```

## The .engspec Format

Every `.engspec` file mirrors a source file with structured sections per function:

```markdown
<!-- engspec v1 -->
<!-- source: src/main.py -->
<!-- language: python -->
<!-- model: claude-opus-4-6 -->
<!-- status: validated -->
<!-- regeneration_count: 7 -->
<!-- regeneration_pass_rate: 5/5 -->

## `function_name(param1: Type, param2: Type) -> ReturnType`

### Purpose
What and why, not how.

### Context
- Called by: caller()
- Calls: callee()
- Test coverage: tested in test_main.py

### Preconditions
- param1 must be non-negative

### Postconditions
- Returns a non-empty list
- Input is not modified

### Invariants
- Pure function, deterministic

### Implementation Notes
- Uses binary search, O(log n)

### Failure Modes
- Raises ValueError if param1 < 0: **propagated** to caller

### Test Strategy
- Property: output is sorted for random inputs
- Edge: empty input returns empty output
```

### Key format features

- **File-level pseudo-functions**: `<file-level: initialization>`, `<file-level: state>` for non-function code
- **Type declarations**: `class Atom(metaclass=ABCMeta)` with full inheritance/interface info
- **Exact literals**: regex patterns, format strings, byte sequences in fenced code blocks
- **Error semantics**: every error labeled **recovered** or **propagated**
- **Test specs**: test files get `.engspec` too, with assertion code blocks in Postconditions

## Validation

Specs are validated through regeneration: re-implement each function from the spec alone 5 times. If all 5 consecutive regenerations produce functionally equivalent code, the spec is validated. Hard cap of 20 total attempts.

## Output Package

The code→engspec pipeline produces a zip containing:

```
project-engspec/
├── project_context.md      # Project description, test setup, etc.
├── call_graph.md            # Function call relationships
├── test_coverage.md         # What's tested, what's not
├── manifest.json            # Index of all specs + non-code files
├── specs/                   # .engspec files mirroring source tree
│   ├── src/
│   │   └── main.py.engspec
│   └── tests/
│       └── test_main.py.engspec
└── non_code/                # Config, docs, assets (verbatim copies)
    ├── pyproject.toml
    ├── README.md
    └── ...
```

## Language Support

Works with any language. The `.engspec` format is English, not tied to any language. Tested with Python repos (python-dotenv, httpx, requests).

## Project Structure

```
engspec_code/
├── engspec_prompt.md              # code → engspec prompt
├── engspec_to_code_prompt.md      # engspec → code prompt
├── engspec_tester_prompt.md       # adversarial debate prompt
├── PLAN.md                        # Detailed design document
├── src/engspec_code/              # Python library (parser, call graph, etc.)
├── tests/                         # Test suite (28 tests)
└── configs/                       # Default configuration
```

## Development

```bash
pip install -e ".[dev]"
pytest tests/
```
