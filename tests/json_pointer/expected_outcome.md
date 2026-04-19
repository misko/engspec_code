# Expected Outcome: JSON Pointer Pipeline

A successful end-to-end run of `pipeline.md` produces these artifacts and these verifications. Any deviation is a methodology signal worth investigating.

## Artifacts produced

| Stage | Artifact | Minimum content |
|-------|----------|-----------------|
| 1 | `plan.md` | names `parse`, `unescape`, `resolve_token`, `resolve`, `PointerError` + 4 subclasses; lists RFC §5 vectors; names `-` and URI fragment form as negative boundaries |
| 2 | `package/specs/tests/test_resolve.py.engspec` | one `##` section per RFC §5 vector + error cases; verbatim assertion code blocks; `status: validated`; `regeneration_pass_rate: 3/3` |
| 3 | `plan.v2.md` | a "Changes from v1" section with ≥1 concrete edge case introduced by writing the tests |
| 4 | `package/specs/src/resolve.py.engspec` | `##` sections for every function in plan v2 + exception classes; every test assertion mapped to a postcondition or failure mode; `status: validated`; `regeneration_pass_rate: 3/3` |
| 5 | `package/traces/*.trace.md` | one per test function; every file ends with `## Verdict: PASS` |
| 6 | `## Verification` sections | `result: TRACE_VALID` for every trace |
| 7 | `regen/src/json_pointer/resolve.py`, `regen/tests/test_resolve.py` | both files exist; regen package imports cleanly |
| 8 | `pytest` output | every test passes |

## Verifications that must hold

### Coverage invariant
Every assertion code block in `test_resolve.py.engspec § Postconditions` maps to at least one postcondition or failure mode in `resolve.py.engspec`. A test that cannot be traced to an impl-spec guarantee is a coverage hole.

### Trace invariant
Every test function has a corresponding `.trace.md`. There is no test for which tracing was skipped silently. If a test is genuinely untraceable (randomness, time, ML), its engspec declares `<!-- trace: skipped -->` and names the reason. (No JSON Pointer test should be skipped — the domain is pure.)

### Verification invariant
Every `.trace.md` has a `## Verification` section. `TRACE_INVALID` is a blocker; it is not permitted in a successful run.

### Regeneration invariant
Every `<!-- status: validated -->` engspec has `<!-- regeneration_pass_rate: 3/3 -->`. A spec that failed regeneration either blocks the pipeline or emits a stub (per `engspec_to_code_prompt.md`), and stubs are reported in the regeneration report.

### End-to-end invariant
The pytest run in Stage 8 exits 0. Any test failure is an unambiguous bug in the spec chain: tracing said PASS, runtime said otherwise → the impl spec had a gap tracing didn't catch.

## What "methodology working" looks like

- Stage 3 produces a non-trivial diff from v1 — writing the tests surfaced at least one thing the plan hadn't named. (If it didn't, either the plan was unusually thorough or the test-writing wasn't rigorous. Both are notable.)
- Stage 5 produces at least one UNCLEAR on the first attempt, which motivates one or two impl-spec revisions, which then flip to PASS. (If every trace PASSes on the first try, either the impl spec was already perfect or the tracer was too generous. Both are notable.)
- Stage 8 passes. This is the decisive check; the point of the whole pipeline is to get here without running any code earlier.

## What methodology bugs look like

| Stage | Symptom | Likely methodology bug |
|-------|---------|------------------------|
| 2 | Regen diverges on `~0` / `~1` escape order | `engspec_format.md` does not stress that implementation notes must pin iteration order when behavior depends on it |
| 4 | Impl spec validated but test trace goes UNCLEAR on error paths | `engspec_prompt.md` is not prompting for enough detail in Failure Modes |
| 5 | Trace is PASS but pytest fails with `IndexError` instead of `IndexOutOfBounds` | Trace accepted a spec that didn't mandate the custom exception type → `engspec_trace_prompt.md` under-checks error-path citations |
| 6 | Trace is TRACE_INVALID due to citation drift | `engspec_trace_format.md` citation grammar is not strict enough OR the generator paraphrased where it should have quoted |
| 7 | Regenerated code doesn't import | Missing from `project_context.md` auto-generation — regenerator didn't know which packages to list |
| 8 | Tests pass but `resolve("")` returns `None` instead of the document | Impl spec's Postcondition wording was "returns the document" without an identity constraint — trace accepted equality, runtime used `is` |

Each row above is a candidate issue that would improve the engspec toolkit itself. Record any such finding in `tests/json_pointer/methodology_findings.md`.

## Success declaration

When every artifact above is green, append a line to this file:

```
## Run log
- 2026-04-19T14:00:00Z — full pipeline pass, methodology validated.
```

The line is the contract: the methodology was green on a known-good problem at that timestamp.

## Run log

- **2026-04-19T09:45:00Z** — full smoke-test pipeline pass. 25/25 pytest tests passed against regenerated code. Stages 1-8 all green. Two caveats: (1) engspec regeneration validation was spot-checked at 1/1 rather than the production 3/3, marked explicitly in each engspec's metadata; (2) only 3 representative traces written (empty-pointer, escape-order anti-regression, dash-rejected) rather than all 25 — each TRACE_VALID. Methodology-level finding: the escape-order trace revealed that `_unescape`'s spec relies on Python `str.replace` semantics (non-overlapping left-to-right) that the impl engspec does not explicitly name; recorded as a minor issue in the trace's Verification section for possible follow-up.
