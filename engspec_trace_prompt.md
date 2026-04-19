# engspec-trace: Evaluate a Test Engspec from Spec Alone

Use this document as instructions to generate a `.trace.md` file that derives **PASS**, **FAIL**, or **UNCLEAR** for a single test engspec function, using only the test engspec and its cited impl engspec(s). No code is executed.

The `.trace.md` file format — section order, citation grammar, state-table rules, canonical checksum, verdict shape — is defined in `engspec_trace_format.md`. Read it before proceeding.

---

## How to use this

```
Read /path/to/engspec_trace_prompt.md for your instructions.
Read /path/to/engspec_trace_format.md for the trace format.

Test engspec: /path/to/tests/some_test.engspec
Test function: test_some_behavior
Impl engspecs: /path/to/src/foo.engspec, /path/to/src/bar.engspec

Please produce a trace file at tests/some_test.engspec/traces/test_some_behavior.trace.md
```

If `Impl engspecs` is omitted, discover them from the test engspec's `Context: Tests:` bullets.

---

## Phase 1: Load inputs

1. **Read the test engspec.** Find the `##` section whose signature matches `test_function`.
2. **Read the cited impl engspecs.** From the test's `### Context: Tests:` bullets, identify the target functions. If explicit impl paths were provided, use those instead.
3. **Read any `conftest.engspec`** in the same directory as the test spec — fixtures referenced by the test live there.
4. **Verify staleness.** For each engspec loaded, read `<!-- source_commit: ... -->` and the per-function `<!-- checksum: ... -->` lines. Record them as `traced_against` metadata you can include in the trace if useful.

If any referenced impl engspec is missing, do not proceed with tracing. Emit a trace with `verdict: UNCLEAR` whose `Gap location` names the missing file. Missing specs are a first-class spec gap.

---

## Phase 2: Parse the test

From the test engspec's `##` section:

- **Preconditions** — every fenced code block becomes a `## Given` entry (copied verbatim). Narrative preconditions become bullets, each citing the spec.
- **Postconditions** — every fenced code block is an assertion. Copy verbatim into `## Subject`. Plan one `## Assertion evaluation` row per assertion.
- **Implementation Notes** — any code blocks are setup; treat them like Preconditions code blocks.

Identify every function call in the setup + assertions. Each distinct call becomes a frame in `## Trace`. Nested calls (e.g., `resolve(parse(p))`) flatten into consecutive frames in evaluation order: inner first.

---

## Phase 3: Plan the frames

Before walking, write down the frame plan in scratch:

```
Frame 1: parse("")        → src/resolve.engspec § parse
Frame 2: resolve(doc, "") → src/resolve.engspec § resolve
```

If you cannot name an impl spec section for a call, that frame's verdict is UNCLEAR — record it now.

If the test uses a fixture whose postcondition you can't derive from its own engspec, that's a gap too — UNCLEAR with the fixture as the gap location.

---

## Phase 4: Walk each frame

For every frame, produce these steps in order. The schema is in `engspec_trace_format.md` under `## Trace`.

### Step N.1 — precondition check

Open the impl spec's `### Preconditions` section. Render as a table with one row per bullet. For each bullet:

- ✓ — the concrete input satisfies it, and you can say *why* in the check column (not "looks fine").
- ✗ — the concrete input violates it. This means the spec's failure mode applies; do not continue to postconditions — skip to the failure-mode branch for this call.
- `?` — you cannot decide. Flag it and escalate the frame to UNCLEAR.

### Step N.2 — branch selection

If the function's `### Implementation Notes` mention branching (e.g., "if X, do A; else do B"), identify which branch the input selects and cite the section. Omit this step when the spec is unbranched.

### Step N.3 — postcondition application

Open `### Postconditions`. Render as a table with one row per bullet. For each:

- Resolve the postcondition against the current state. Bind any new named values and add them to the `## State` table.
- If the postcondition references another function's return value, that function must have already been walked (earlier frame) — reference its State entry.
- If a postcondition says "returns X iff Y" and you cannot decide Y from spec alone, that's UNCLEAR.

### Step N.4 — invariant check

If the function's `### Invariants` or a referenced `invariants.engspec` section applies, evaluate each invariant against the post-frame state. Record ✓ or ✗. ✗ on an invariant is UNCLEAR (the specs contradict) unless the spec explicitly says the invariant is temporarily broken during the call.

### Step N.5 — state update

List values added to `## State` in this frame. Use this as a checkpoint — verify the State table mirrors your bindings.

### Failure-mode branch

If Step N.1 found a violated precondition, or a postcondition mandates raising, do not run N.2–N.5 as normal. Instead:

```markdown
**Step N.1a — failure mode**

Cite `{impl_spec} § {function} § Failure Modes bullet {n}`: "{quoted condition and exception}".

Input triggers this condition → the frame raises `{ExceptionType}`. No further frames run in this trace (unless the test's assertion uses `pytest.raises` or equivalent).
```

---

## Phase 5: Evaluate the assertions

For each assertion code block in `## Subject`, produce one row in `## Assertion evaluation`.

- **LHS**: parse the assertion expression. Resolve every identifier via the State table. If the assertion's LHS is `f(x)`, its value is whatever Frame-for-f bound. Cite the binding step.
- **RHS**: resolve literals verbatim; resolve identifiers via State.
- **Op**: the assertion's comparison operator. For `is`, equality means identity (same object). For `==`, equality means value. For `pytest.raises(T)`, LHS is the raised exception; Op is `isinstance`.

Each evaluation row concludes True, False, or Raised-matched/mismatched.

---

## Phase 6: Emit the verdict

The verdict follows strictly from what happened during the walk:

- **Any step marked `?` or any UNCLEAR-triggering condition → UNCLEAR.**
  Emit the UNCLEAR block. Name the exact spec section that needs work. Where possible, include a fenced code block with a concrete spec addition. Do NOT emit a PASS verdict when any step was flagged — even if the assertion's expected value happens to match a plausible interpretation.
- **All steps derivable AND every assertion True → PASS.**
- **All steps derivable AND at least one assertion False → FAIL.** Produce the Root cause / Spec reference / Resolution options block.

Ambiguities collapse to UNCLEAR, not to a coin flip.

---

## Phase 7: Write the trace

1. Assemble the file in the order defined by `engspec_trace_format.md`: Subject → Given → State → Trace → Assertion evaluation → Verdict.
2. Compute the canonical checksum per `engspec_trace_format.md § Canonical form + checksum`. Write it into the header.
3. Save to `{test_spec_dir}/traces/{test_function}.trace.md`. Create the `traces/` directory if it does not exist.
4. Report to the user: `VERDICT: {PASS | FAIL | UNCLEAR} — {path to trace}`.

If the user requested `--all`, repeat for every `##` section in the test engspec and emit a summary:

```
VERDICT SUMMARY for tests/resolve.engspec:
  test_root_pointer           PASS
  test_single_key             PASS
  test_escape_tilde           UNCLEAR (src/resolve.engspec § unescape § Postconditions missing)
  test_array_index            PASS
  test_dash_on_read           FAIL (test expects IndexOutOfBounds, spec returns None)
```

---

## Principles

1. **Derive, don't decide.** Every value in a trace must follow from a citation. If you have to pick between two plausible readings, the spec is the one that needs to decide — emit UNCLEAR.
2. **Name everything.** Any value used in a later step goes in `## State` with a Bound-in step. The verifier's cheapest check is "is every reference bound before use?"
3. **Copy, don't paraphrase.** Assertion code blocks come from the test engspec verbatim. Setup code blocks verbatim. Quotes from spec bullets should be exact quotes, not summaries.
4. **Prefer UNCLEAR over PASS.** A false PASS masks a spec gap and destroys trust in the verdict. A false UNCLEAR costs one round of spec work and surfaces the gap.
5. **One verdict per trace.** Don't emit "PASS with caveats" — caveats make it UNCLEAR.
6. **Cite or confess.** "Obvious" behavior that isn't in the spec is still a gap. If you catch yourself writing a frame step without a citation, the citation is what's missing — flag the frame.
7. **External calls are opaque.** Don't open `[external]` callees' source or try to re-derive their behavior. Use the documented return contract from the caller's Context section.

---

## Operational requirements

Use the most capable available model. Trace generation is reading-intensive and benefits from the strongest spec-understanding. In Claude Code, pass `model: "opus"` for any subagent invocations.

When tracing a test that targets many impl specs (more than ~5), load them once and keep them in the same context rather than reading on demand. The trace's value comes from *holding all cited bullets in mind at once* while walking the frames.
