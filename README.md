# engspec_code

English-first specification layer for any codebase. Every function gets a parallel `.engspec` specification written in structured English, detailed enough that an AI agent can re-implement the function from the spec alone.

No installation required. Three self-contained markdown prompts — give them to Claude and go.

## The Pipeline

```
engspec_prompt.md          →  code → engspec (produces project-engspec.zip)
engspec_tester_prompt.md   →  adversarial debate (strengthens specs)
engspec_to_code_prompt.md  →  engspec → code (regenerates codebase from specs)
```

## Prompts

### 1. `engspec_prompt.md` — Code → Engspec

Analyzes a codebase and produces validated `.engspec` files for every source and test file. Validates each spec by reimplementing from spec alone 5 times.

**Example — from a git URL:**

```
Read /path/to/engspec_prompt.md for your instructions.

Please clone https://github.com/encode/httpx, analyze the repo, and produce validated .engspec files for all source files.

No input.md is provided — auto-generate the project context from the repo.
```

**Example — from a local repo:**

```
Read /path/to/engspec_prompt.md for your instructions.

Here is my repo at /home/ubuntu/my-project

Please produce validated .engspec files for all source files.
```

**Output:** `project-engspec.zip` containing `.engspec` files, project context, call graph, test coverage analysis, non-code files (configs, docs, assets), and a manifest.

---

### 2. `engspec_tester_prompt.md` — Adversarial Debate

Runs Red/Blue/Judge debate on `.engspec` files to find spec gaps, ambiguities, and contradictions. The Judge never sees source code — if the spec is too ambiguous to rule on, that's a finding.

**Example — spec + source (recommended):**

```
Read /path/to/engspec_tester_prompt.md for your instructions.

Here is the engspec package at: /home/ubuntu/httpx-engspec
Here is the source repo at: /home/ubuntu/httpx

Please run adversarial analysis.
```

**Example — spec only:**

```
Read /path/to/engspec_tester_prompt.md for your instructions.

Here is the engspec package at: /home/ubuntu/httpx-engspec

Please run adversarial analysis.
```

**Output:** Updated `.engspec` files with Debate Log entries and fixes, analysis report with findings and confidence scores.

---

### 3. `engspec_to_code_prompt.md` — Engspec → Code

Regenerates a full working codebase from an `.engspec` package. Installs dependencies first (so third-party APIs can be introspected), regenerates in dependency order, then runs tests.

**Example:**

```
Read /path/to/engspec_to_code_prompt.md for your instructions.

Here is the engspec package: /home/ubuntu/httpx-engspec.zip

Please regenerate the full codebase into /home/ubuntu/httpx-regen/ and run tests.
```

**Output:** Complete working codebase + test results + validation report listing any spec gaps found during regeneration.

---

## The .engspec Format

```markdown
<!-- engspec v1 -->
<!-- source: src/main.py -->
<!-- language: python -->
<!-- model: claude-opus-4-6 -->
<!-- status: validated -->
<!-- regeneration_count: 7 -->
<!-- regeneration_pass_rate: 3/3 -->

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

### Key features

- **Language-agnostic** — works with any codebase (tested on Python repos)
- **File-level pseudo-functions** — `<file-level: initialization>`, `<file-level: state>` for non-function code
- **Type declarations** — `class Atom(metaclass=ABCMeta)` with full inheritance info
- **Exact literals** — regex patterns, byte sequences in fenced code blocks (never paraphrased)
- **Error semantics** — every error labeled **recovered** or **propagated** with exact error type
- **Test specs** — test files get `.engspec` too, with assertion code blocks in Postconditions
- **Negative boundaries** — what the function does NOT implement is as important as what it does

## Validation

Specs are validated through regeneration: re-implement each function from the spec alone. Must achieve **3 consecutive passes** within **20 total attempts**. Any failure refines the spec and resets the counter.

## Tested On

- [python-dotenv](https://github.com/theskumar/python-dotenv)
- [httpx](https://github.com/encode/httpx)
- [requests](https://github.com/psf/requests)

## Repository Contents

```
engspec_code/
├── engspec_prompt.md              # code → engspec
├── engspec_to_code_prompt.md      # engspec → code
├── engspec_tester_prompt.md       # adversarial debate
└── README.md
```
