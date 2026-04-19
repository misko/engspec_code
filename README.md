# engspec

English-first specification layer for any codebase.

You don't need to read a fused Triton kernel to understand what a neural network layer does. You need to know: what tensors go in, what tensors come out, what mathematical operation is performed, what numerical properties are preserved, and how it's tested. The implementation details — block sizes, memory layouts, warp-level optimizations — matter for performance, but the specification is what tells you whether the code is *correct*.

engspec captures this as structured English. Every function gets a specification covering its contract (preconditions, postconditions, invariants), its failure modes, and its test strategy. The spec is shorter than the code, readable by anyone, and precise enough to regenerate a working implementation from scratch.

Convert any codebase to `.engspec` files. Let adversarial AI agents debate every edge case, error path, and parameter contract. Give high-level guidance in plain English — "this implements SO(3)-equivariant message passing, not SE(3)" — and the agents handle implementation, testing, and validation. You steer at the level of mathematical intent; they work out the details.

No installation required. Three markdown prompts and one shared format spec — give them to Claude and go.

## Quick Start (Claude Code)

If you're using Claude Code, the repo includes slash commands:

```bash
# Spec an entire repo
/engspec /home/ubuntu/my-project

# Spec specific files only
/engspec /home/ubuntu/my-project src/parser.py src/lexer.py

# Update specs for changed files
/engspec /home/ubuntu/my-project --incremental /home/ubuntu/my-project-engspec/

# Run adversarial debate on specs
/engspec-test /home/ubuntu/my-project-engspec /home/ubuntu/my-project

# Spec-only mode (no source)
/engspec-test /home/ubuntu/my-project-engspec

# Regenerate code from specs
/engspec-regen /home/ubuntu/my-project-engspec.zip

# Regenerate partial package into existing codebase
/engspec-regen /home/ubuntu/my-project-engspec /home/ubuntu/my-project
```

Not using Claude Code? See the [Prompts](#prompts) section below for manual usage.

## The Pipeline

```
engspec_prompt.md                →  code → engspec (produces project-engspec.zip)
engspec_trace_prompt.md          →  (test + impl engspecs) → PASS/FAIL/UNCLEAR trace
engspec_verify_trace_prompt.md   →  trace → TRACE_VALID / TRACE_INVALID / TRACE_STALE
engspec_tester_prompt.md         →  adversarial debate (strengthens specs)
engspec_to_code_prompt.md        →  engspec → code (regenerates codebase from specs)
```

Tracing is the cheapest validator: it runs **before** adversarial debate and **before** any code exists, and its UNCLEAR verdict names the exact spec section that needs strengthening. A PASS trace proves that the test engspec's assertion can be derived from the impl engspec alone — that any correct implementation of the spec would pass the test.

## Prompts

### 1. `engspec_prompt.md` — Code → Engspec

Analyzes a codebase and produces validated `.engspec` files. Supports full, partial (subset of files), and incremental (update changed files only) modes. Validates each spec by reimplementing from spec alone 3 times.

**Example — full repo:**

```
Read /path/to/engspec_prompt.md for your instructions.
Here is my repo at /home/ubuntu/my-project
Please produce validated .engspec files for all source files.
```

**Example — partial (specific files):**

```
Read /path/to/engspec_prompt.md for your instructions.
Here is my repo at /home/ubuntu/my-project
Please produce .engspec files for only: src/parser.py, src/lexer.py
```

**Example — incremental update:**

```
Read /path/to/engspec_prompt.md for your instructions.
Here is my repo at /home/ubuntu/my-project
Here is the existing engspec package at: /home/ubuntu/my-project-engspec/
Please update specs for files that have changed.
```

**Output:** `project-engspec.zip` containing `.engspec` files, project context, call graph, test coverage analysis, non-code files (configs, docs, assets), and a manifest.

---

### 2. `engspec_tester_prompt.md` — Adversarial Debate

Runs Red/Blue debate with a two-Judge system on `.engspec` files to find spec gaps, ambiguities, and contradictions. The Blind Judge rules from spec only (tests self-containment); the Sighted Judge rules with source access (tests accuracy). Disagreements between them are the highest-value findings.

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

### 2a. `engspec_trace_prompt.md` — Evaluate a Test Engspec from Spec Alone

Generates a `.trace.md` that derives **PASS**, **FAIL**, or **UNCLEAR** for a single test engspec function, using only the test engspec and its cited impl engspec(s). No code is executed. The trace is a mechanical derivation — every step cites a specific spec bullet, every intermediate value is named in a `## State` table, and the verdict follows strictly from whether all steps are derivable and all assertions hold.

**Example:**

```
Read /path/to/engspec_trace_prompt.md for your instructions.
Read /path/to/engspec_trace_format.md for the trace format.

Test engspec: /path/to/tests/test_resolve.py.engspec
Test function: test_root_pointer
Impl engspec: /path/to/src/resolve.py.engspec

Please produce a trace.
```

**Output:** `{test_spec_dir}/traces/{test_function}.trace.md`. Verdict is one of PASS (spec sufficient for this assertion), FAIL (test and spec disagree), or UNCLEAR (spec has a gap).

**When to use it:** after the impl engspec is written but before adversarial debate. An UNCLEAR verdict names the cheapest kind of spec gap — something missing before any code exists. A FAIL verdict names a test/spec disagreement that must be resolved before proceeding.

---

### 2b. `engspec_verify_trace_prompt.md` — Verify a Trace

Reads an existing `.trace.md` and checks that each step is locally sound given the cited engspecs: citations resolve, state references are bound before use, the verdict matches the assertion evaluation table. Appends a `## Verification` section with **TRACE_VALID**, **TRACE_INVALID**, or **TRACE_STALE**.

Separating verification from generation matters: the verifier produces its ruling without having committed to an answer, making TRACE_VALID a meaningful signature.

**Example:**

```
Read /path/to/engspec_verify_trace_prompt.md for your instructions.
Read /path/to/engspec_trace_format.md for the trace format.

Trace file: /path/to/tests/test_resolve.py.engspec/traces/test_root_pointer.trace.md

Please verify this trace.
```

**Output:** the same trace file with a `## Verification` block appended (excluded from the trace's checksum, so re-verification is safe).

---

### 3. `engspec_to_code_prompt.md` — Engspec → Code

Regenerates a full working codebase from an `.engspec` package. Installs dependencies first (so third-party APIs can be introspected), regenerates in dependency order, then runs tests.

**Example — full package:**

```
Read /path/to/engspec_to_code_prompt.md for your instructions.
Here is the engspec package: /home/ubuntu/httpx-engspec.zip
Please regenerate the full codebase into /home/ubuntu/httpx-regen/ and run tests.
```

**Example — partial package (regenerate into existing codebase):**

```
Read /path/to/engspec_to_code_prompt.md for your instructions.
Here is the engspec package: /home/ubuntu/httpx-engspec/
Here is the existing codebase at: /home/ubuntu/httpx/
Please regenerate only the spec'd files into the existing codebase.
```

**Output:** Complete working codebase + test results + validation report listing any spec gaps found during regeneration.

---

## The .engspec Format

The full format specification is in `engspec_format.md`. Here's the structure at a glance:

```markdown
<!-- engspec v1 -->
<!-- source: src/main.py -->
<!-- language: python -->
<!-- model: claude-opus-4-6 -->
<!-- status: validated -->
<!-- source_commit: a1b2c3d4... -->
<!-- regeneration_count: 7 -->
<!-- regeneration_pass_rate: 3/3 -->

## `function_name(param1: Type, param2: Type) -> ReturnType`
<!-- checksum: 9f86d081884c... -->
<!-- audited: 2026-03-15T14:00:00Z -->

### Purpose
What and why, not how.

### Context / Preconditions / Postconditions / Invariants
### Implementation Notes / Failure Modes / Test Strategy

### Debate Log  (added by engspec_tester only)
| Round | Finding | Blind | Sighted | Tag | Severity | Action |
```

### Key features

- **Language-agnostic** — works with any codebase (tested on Python repos)
- **File-level pseudo-functions** — `<file-level: initialization>`, `<file-level: state>` for non-function code
- **Type declarations** — `class Atom(metaclass=ABCMeta)` with full inheritance info
- **Exact literals** — regex patterns, byte sequences in fenced code blocks (never paraphrased)
- **Error semantics** — every error labeled **recovered** or **propagated** with exact error type
- **Test specs** — test files get `.engspec` too, with assertion code blocks in Postconditions
- **Negative boundaries** — what the function does NOT implement is as important as what it does
- **Per-function versioning** — MD5 checksums detect spec drift; `source_commit` tracks which source version the spec was written against
- **Two-Judge adversarial debate** — Blind Judge (spec only) and Sighted Judge (spec + source) catch both ambiguity and silent divergence

## Validation

Specs are validated through regeneration: re-implement each function from the spec alone. Must achieve **3 consecutive passes** within **20 total attempts**. Any failure refines the spec and resets the counter.

## Tested On

- [python-dotenv](https://github.com/theskumar/python-dotenv)
- [httpx](https://github.com/encode/httpx)
- [requests](https://github.com/psf/requests)

## Repository Contents

```
engspec_code/
├── engspec_format.md                  # shared format for .engspec files (v1.0)
├── engspec_prompt.md                  # code → engspec
├── engspec_to_code_prompt.md          # engspec → code
├── engspec_tester_prompt.md           # adversarial debate
├── engspec_trace_format.md            # shared format for .trace.md files (v1.0)
├── engspec_trace_prompt.md            # (test + impl specs) → PASS/FAIL/UNCLEAR trace
├── engspec_verify_trace_prompt.md     # trace → TRACE_VALID/INVALID/STALE
├── tests/
│   └── json_pointer/                  # end-to-end pipeline smoke test
│       ├── idea.md                    # stage-1 input
│       ├── pipeline.md                # 8-stage runbook
│       ├── expected_outcome.md        # success criteria
│       └── rfc6901_vectors.md         # RFC 6901 §5 test vectors (verbatim)
└── README.md
```

## End-to-end smoke test

`tests/json_pointer/` drives the full methodology — idea → plan → test engspec → re-plan → impl engspec → trace → verify trace → regenerate code → run tests — against a [RFC 6901](https://www.rfc-editor.org/rfc/rfc6901) JSON Pointer resolver. The RFC provides ground-truth test vectors; the pipeline finishes when every generated test passes the regenerated code. Any stage that fails identifies exactly where the methodology is weak. See `tests/json_pointer/pipeline.md` for the runbook and `tests/json_pointer/expected_outcome.md` for the success criteria.
