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

## Building from scratch: idea → running code

The full methodology is a loop from an English idea to validated, tested code. Each arrow below is an artifact handoff; each stage's failure mode tells you which earlier stage to iterate on.

```
idea  →  plan  →  test engspecs  →  revise plan  →  impl engspecs  →  trace + pytest  →  iterate
```

A worked example of every stage lives under [`tests/json_pointer/`](tests/json_pointer/) — RFC 6901 JSON Pointer resolver, 25/25 generated tests passing.

### 1. Idea

Write one page describing what you want: public API shape, what's in scope, what's out of scope. Reference external specs by name (RFCs, standards) rather than paraphrasing them. See [`tests/json_pointer/idea.md`](tests/json_pointer/idea.md).

**Artifact:** `idea.md`. **No dedicated prompt** — the idea is human input.

### 2. Plan

A regular Claude session consumes the idea and produces a plan: module layout, function signatures, test strategy, edge cases, ambiguities flagged for human resolution. Review it. Amend before continuing.

**Artifact:** `plan.md`. **No dedicated prompt** yet — use a normal session.

### 3. Test engspecs

Using [`engspec_prompt.md`](engspec_prompt.md), produce `.engspec` files for the test suite *before* writing implementation code. Every assertion is a verbatim code block in Postconditions. Validated by 3 consecutive regenerations from spec alone producing byte-equivalent assertions.

Source code does not exist yet — this is deliberate. Writing tests first surfaces design decisions that would otherwise hide in the implementation.

**Artifact:** `tests/*.engspec` files with `<!-- status: validated -->`.

### 4. Revise plan

Writing the test specs almost always surfaces edge cases the plan did not name — error types, ordering decisions, fixture locations, base-class catch behavior. Re-read the plan against the test specs and produce a revision with an explicit "Changes from v1" section. If nothing changed, either your plan was exceptional or stage 3 was not rigorous — both are worth noticing.

**Artifact:** `plan.v2.md`.

### 5. Impl engspecs

Using [`engspec_prompt.md`](engspec_prompt.md) again, against the revised plan + test engspecs, produce `.engspec` files for the source code. Every assertion in the test engspecs must map to a postcondition or failure mode in some impl engspec — build a coverage table in the revised plan to check this. Validated by 3/3 regeneration.

**Artifact:** `src/*.engspec` files.

### 6. Trace + pytest

Two validators run at this stage, cheap-to-expensive:

- **Trace each test.** Using [`engspec_trace_prompt.md`](engspec_trace_prompt.md), produce one `.trace.md` per test function — deriving PASS, FAIL, or UNCLEAR from the specs alone, no code executed. Using [`engspec_verify_trace_prompt.md`](engspec_verify_trace_prompt.md), a second Claude proof-checks each trace into TRACE_VALID. **Most iteration happens here.** An UNCLEAR verdict names the exact impl-spec section that needs strengthening. A FAIL names a test/spec disagreement.

- **Regenerate and run.** Using [`engspec_to_code_prompt.md`](engspec_to_code_prompt.md), produce source + test files + build config from the spec package. Run the tests. Every pass is expected — tracing already predicted it. Any failure is a real methodology finding: tracing said PASS, runtime said otherwise → the impl spec has a gap tracing did not catch.

**Artifacts:** `traces/*.trace.md` and a regenerated codebase that passes its own tests.

### 7. (Optional) Adversarial debate

Using [`engspec_tester_prompt.md`](engspec_tester_prompt.md), run Red/Blue/Judge debate over the package. Findings on a traced-clean package are the highest-signal you get — the gaps every cheap validator missed. Apply the findings, re-trace, re-regen.

### Iterate — which stage to revisit when something fails

| Failure | Iterate at |
|---|---|
| Stage 3 test spec does not converge to 3/3 regeneration | Stage 3 — test spec is ambiguous; add verbatim code blocks, tighten preconditions |
| Stage 5 impl spec does not converge to 3/3 regeneration | Stage 5 — two reasonable reimplementations differ; name the missing detail in Implementation Notes |
| Stage 6 trace verdict UNCLEAR | Stage 5 — impl spec has a named gap; fix the cited section, re-trace |
| Stage 6 trace verdict FAIL | Stage 3 or 5 — test and impl spec disagree; trace names both options, pick one |
| Stage 6 verifier rules TRACE_INVALID | Stage 6 — regenerate the trace with a fresh agent |
| Stage 6 pytest fails after all traces PASS | Stage 5 — spec gap that tracing missed (rare, most valuable finding); record as a methodology finding |
| Stage 7 adversarial finding | Stage 3 or 5 per the finding's target |

The whole methodology is leverage from moving discovery earlier. A spec gap caught at stage 6 costs one edit. The same gap caught at stage 7's pytest costs an edit plus a full regeneration plus a test re-run. The same gap caught in production costs whatever it broke.

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
