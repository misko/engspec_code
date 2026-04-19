# JSON Pointer End-to-End Pipeline

This runbook drives the JSON Pointer idea through the full engspec pipeline — eight stages, each a Claude session whose output is the next stage's input. Success at every stage means the engspec methodology (including the new tracing step) works end-to-end on a real problem.

**Who this is for:** a human (or a supervising Claude) running a smoke test of the engspec toolkit. Each stage has a specific prompt to paste, a specific output artifact to check, and a specific success criterion.

---

## Working directory

All stages run under `~/gits/engspec_code/tests/json_pointer/`. The final regenerated code lives at `~/gits/engspec_code/tests/json_pointer/regen/`.

Expected artifacts at each stage:

```
tests/json_pointer/
├── idea.md                      stage 0 input
├── pipeline.md                  this file
├── expected_outcome.md          success criteria
├── rfc6901_vectors.md           test data
├── plan.md                      stage 1 output
├── plan.v2.md                   stage 3 output (re-plan after tests)
├── package/                     engspec package — grows through stages 2 and 4
│   ├── project_context.md
│   ├── call_graph.md
│   ├── test_coverage.md
│   ├── manifest.json
│   ├── specs/
│   │   ├── src/
│   │   │   └── resolve.py.engspec
│   │   └── tests/
│   │       └── test_resolve.py.engspec
│   └── traces/
│       ├── test_resolve_root.trace.md
│       ├── test_resolve_single_key.trace.md
│       └── ...
└── regen/                       stage 7 output — the actual Python package
    ├── pyproject.toml
    ├── src/json_pointer/
    │   └── resolve.py
    └── tests/
        └── test_resolve.py
```

---

## Stage 1: idea → plan

**Input:** `idea.md`

**Prompt to paste into Claude:**

```
I'm exploring building a small library. Here's the idea:

<paste contents of idea.md>

Please produce a plan at tests/json_pointer/plan.md. The plan should cover:
- Module layout (which files, which functions)
- Test strategy (what categories of tests, example cases)
- Edge cases worth pinning down before writing engspecs
- Anything ambiguous in the idea I should resolve
```

**Output:** `plan.md`

**Success criterion:** plan names every function that will appear in the impl engspec (roughly: `parse`, `unescape`, `resolve_token`, `resolve`, plus the exception classes), lists all RFC 6901 §5 vectors as reference tests, and calls out the `-` index and URI fragment form as explicit negative boundaries.

**Human gate:** review the plan for anything the idea got wrong. Answer any clarification questions before proceeding.

---

## Stage 2: plan → test engspecs

**Input:** `plan.md`, `rfc6901_vectors.md`, `engspec_prompt.md`, `engspec_format.md`

**Prompt:**

```
Read engspec_prompt.md and engspec_format.md for your instructions.

I have a plan at tests/json_pointer/plan.md and test vectors at
tests/json_pointer/rfc6901_vectors.md. Source code does not exist yet.

Please produce a validated test engspec at
tests/json_pointer/package/specs/tests/test_resolve.py.engspec.

Each RFC 6901 §5 vector should become its own test function, with the
assertion as a verbatim code block in Postconditions. Error cases from
rfc6901_vectors.md similarly. Do NOT generate implementation code.

The spec must be validated: 3 consecutive regenerations of the test file
from spec alone produce equivalent test code (same assertions verbatim).
```

**Output:** `package/specs/tests/test_resolve.py.engspec` with `<!-- status: validated -->` and `<!-- regeneration_pass_rate: 3/3 -->`.

**Success criterion:** every RFC vector has a `##` test-function section with a verbatim assertion code block in Postconditions. Error cases use `pytest.raises`. Status is `validated`.

---

## Stage 3: re-plan

**Input:** `plan.md` + test engspec from Stage 2

**Prompt:**

```
Here is the original plan at tests/json_pointer/plan.md and the validated
test engspec at tests/json_pointer/package/specs/tests/test_resolve.py.engspec.

Writing the tests likely revealed edge cases the plan didn't name (e.g.,
what exactly does "bad index format" mean? what about whitespace-only
pointers? what about non-string keys?).

Please produce a revised plan at tests/json_pointer/plan.v2.md. Show a
diff summary of what changed and why. This revision informs the impl
engspec we write next.
```

**Output:** `plan.v2.md` with a leading "Changes from v1" section.

**Success criterion:** plan.v2.md cites at least one edge case that arose from writing the tests. If nothing changed, the re-plan either wasn't rigorous or the original plan was unusually complete — both are notable.

---

## Stage 4: plan.v2 + test specs → impl engspec

**Input:** `plan.v2.md`, test engspec

**Prompt:**

```
Read engspec_prompt.md and engspec_format.md.

Plan: tests/json_pointer/plan.v2.md
Tests: tests/json_pointer/package/specs/tests/test_resolve.py.engspec

Please produce a validated implementation engspec at
tests/json_pointer/package/specs/src/resolve.py.engspec.

Every assertion in the test engspec must be satisfied by some postcondition
or failure mode in the impl engspec. If an assertion is not covered, add
a postcondition; do not drop the assertion.

Validate via 3/3 regeneration. Source code still does not exist — the
regenerator produces Python from the spec alone, compares against the
test engspec's expected behavior (no execution).
```

**Output:** `package/specs/src/resolve.py.engspec` with `validated` status.

**Success criterion:** every test-engspec assertion maps to a postcondition in the impl spec. Every error class has its own `##` section. Functions named in `plan.v2.md` all have sections.

---

## Stage 5: run traces

**Input:** test engspec + impl engspec + `engspec_trace_prompt.md` + `engspec_trace_format.md`

**Prompt (once per test function, or use `--all`):**

```
Read engspec_trace_prompt.md for your instructions.
Read engspec_trace_format.md for the trace format.

Test engspec: tests/json_pointer/package/specs/tests/test_resolve.py.engspec
Test function: <name> (or: --all for every function)
Impl engspec: tests/json_pointer/package/specs/src/resolve.py.engspec

Please produce traces at tests/json_pointer/package/traces/.
```

**Output:** one `.trace.md` per test function under `package/traces/`. Every verdict must be `PASS`.

**Success criterion:** every `.trace.md` ends with `## Verdict: PASS`.

**Failure mode — UNCLEAR:** fix the impl engspec where the UNCLEAR points, re-validate it (3/3 regen), re-run the affected traces. Loop until all PASS.

**Failure mode — FAIL:** either the test is wrong or the impl spec contradicts the test. Pick one to fix per the trace's Resolution options, re-run.

---

## Stage 6: verify traces

**Input:** traces from Stage 5

**Prompt:**

```
Read engspec_verify_trace_prompt.md for your instructions.
Read engspec_trace_format.md for the trace format.

Please verify every trace under tests/json_pointer/package/traces/.
```

**Output:** each trace file has a `## Verification` section appended with `result: TRACE_VALID`.

**Success criterion:** 100% TRACE_VALID. Any TRACE_INVALID means the generator produced a trace that doesn't hold up to proof-checking — regenerate that trace.

---

## Stage 7: engspec → code

**Input:** full engspec package, `engspec_to_code_prompt.md`

**Prompt:**

```
Read engspec_to_code_prompt.md for your instructions.

Here is the engspec package: tests/json_pointer/package/

Please regenerate the full codebase into tests/json_pointer/regen/ and
run the tests.
```

**Output:** `tests/json_pointer/regen/src/json_pointer/resolve.py` and `tests/json_pointer/regen/tests/test_resolve.py`.

**Success criterion:** the regenerated code imports cleanly (`python -c "from json_pointer import resolve"` works) and every test file exists.

---

## Stage 8: run the generated tests

**Input:** regenerated code

**Command (human runs this):**

```bash
cd ~/gits/engspec_code/tests/json_pointer/regen
pip install -e .
pytest -v
```

**Success criterion:** every test passes.

A failure here means the impl engspec is underspecified in a way tracing did not catch — the trace accepted something the runtime rejected. This is the most valuable finding the whole pipeline produces, because it names a gap that all three cheap validators (regeneration, tracing, adversarial debate) missed. Feed it back to `idea.md` and start again.

---

## The "all-green" outcome

A full successful run produces:
- `plan.md`, `plan.v2.md` (re-plan showed something)
- Validated test engspec (3/3)
- Validated impl engspec (3/3)
- One PASS trace per test
- One TRACE_VALID verification per trace
- Regenerated code that passes every test

If every item above is green, the methodology (including the new tracing step) is validated end-to-end on a real problem. If any item is red, the red is exactly where methodology-level attention is needed — not on JSON Pointer, on the pipeline itself.

---

## Optional Stage 9: adversarial debate

For completeness, after the pipeline passes once, run `engspec_tester_prompt.md` over the validated package. Debate findings on a package that traced clean and tested clean are high-signal — they're gaps none of the other validators caught.

```
Read engspec_tester_prompt.md for your instructions.

Engspec package: tests/json_pointer/package/
Source repo: tests/json_pointer/regen/

Please run adversarial analysis.
```

Zero critical findings on this tiny project would be a positive methodology signal. A critical finding would be an opportunity to improve `engspec_prompt.md` or `engspec_trace_prompt.md`.
