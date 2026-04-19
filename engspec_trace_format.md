# engspec Trace Format Specification v1.0

Reference document defining the `.trace.md` file format. Referenced by:
- `engspec_trace_prompt.md` — produces `.trace.md` files from a test engspec + impl engspec(s)
- `engspec_verify_trace_prompt.md` — reads a `.trace.md` and appends a verification ruling

A trace answers one question: **given these specs and this input, what does the specification say happens?** It is a mechanical derivation, not a measurement. Three verdicts are possible:

| Verdict | Meaning |
|---------|---------|
| **PASS** | Every derivation step follows from the cited spec bullets; the final assertion holds. Any correct implementation of the spec would pass this test. |
| **FAIL** | Every step follows, but the specs derive a value that does not satisfy the assertion. The test and the impl spec actively disagree. |
| **UNCLEAR** | At least one step cannot be derived — a cited section is missing, ambiguous, or allows multiple outputs. **This is the most valuable output**: it names a spec gap before any code is written. |

A **PASS** does not mean the implementation is correct. It means the spec is sufficient for the assertion. Implementation correctness is established by `engspec_to_code_prompt.md` regeneration passing the generated tests.

---

## File-Level Metadata

Every `.trace.md` file starts with metadata as HTML comments:

```markdown
<!-- engspec-trace v1 -->
<!-- test_spec: {relative/path/to/test.engspec} -->
<!-- test_function: {name of the ## section being traced} -->
<!-- impl_specs: {comma-separated list of impl engspec paths} -->
<!-- traced_by: {model identifier, e.g. claude-opus-4-7} -->
<!-- traced_at: {ISO 8601 timestamp} -->
<!-- verdict: {PASS | FAIL | UNCLEAR} -->
<!-- checksum: {MD5 hex digest of canonical trace body} -->
```

If any cited engspec's `source_commit` is newer than `traced_at`, the trace is **stale** — the verifier flags it for regeneration rather than verifying its claims.

---

## Section Order

Every trace file has these sections, in this order. Do not rename, reorder, or omit any of them. Sections that have nothing to record use a single bullet `- none` rather than disappearing — the verifier relies on the structure.

```
## Subject
## Given
## State
## Trace
   ### Frame 1: {operation}
   ### Frame 2: {operation}
   ...
## Assertion evaluation
## Verdict: {PASS | FAIL | UNCLEAR}
## Verification               (appended by verifier, not by generator)
```

---

## `## Subject`

The test's assertion code block(s), copied verbatim from the test engspec's `### Postconditions`. If the test has multiple assertion code blocks, they appear here in the order they appear in the spec, separated by blank lines. The verifier checks this section byte-for-byte against the test engspec.

```markdown
## Subject

```python
assert resolve(doc, "") is doc
```
```

---

## `## Given`

Enumerates what the trace takes as established before Frame 1 runs. Each bullet cites its source. Three kinds of entries:

1. **Fixture outcomes** — cite the fixture's postconditions from the test engspec or a `conftest.engspec`.
2. **Setup code blocks** — copied verbatim from the test engspec's Preconditions / Implementation Notes.
3. **Values bound by the test input** — named literals introduced by the test (e.g., `doc = {"foo": ["bar", "baz"]}`).

```markdown
## Given
- `doc = {"foo": ["bar", "baz"]}` — from tests/resolve.engspec § test_root_pointer § Preconditions.
- No further fixtures.
```

---

## `## State`

A single table that holds every named value bound during the trace. The generator writes rows as values are introduced; the verifier uses this table to confirm later references resolve to an earlier binding.

| Column | Meaning |
|--------|---------|
| `Name` | The identifier used when the value is referenced later. Lowercase snake_case. |
| `Bound in` | `Frame N Step N.M` or `Given` for pre-trace values. |
| `Value / description` | A concrete value (literal) or a description precise enough that an independent reader could reconstruct it. |

```markdown
## State

| Name | Bound in | Value / description |
|---|---|---|
| `doc` | Given | `{"foo": ["bar", "baz"]}` |
| `tokens` | Frame 1 Step 1.3 | `[]` — empty list (pointer was `""`) |
| `result` | Frame 2 Step 2.2 | `doc` — root of the document |
```

**Verifier rule:** every name referenced in a frame step must appear in the State table with `Bound in` strictly earlier than the referring step.

---

## `## Trace`

Contains one `### Frame N: {operation}` subsection per function call in the test's setup + assertion. Within each frame, steps are numbered `N.1`, `N.2`, … and follow this structure:

```markdown
### Frame N: {signature or concise description}

**Call** — `{function_name}({concrete args})`
**Cite** — `{impl_spec path} § {function_name}`

**Step N.1 — precondition check**

| # | Bullet from spec | Check against input | ✓/✗/? |
|---|---|---|---|
| 1 | "{quoted or paraphrased precondition}" | {concrete check} | ✓ |
| 2 | ... | ... | ✗ → {what this implies} |

**Step N.2 — branch selection** (omit if spec is unbranched)

Cite `{impl_spec}:{function} § Implementation Notes` for the branching criterion. Name which branch the input selects.

**Step N.3 — postcondition application**

| # | Postcondition | Resolved state / return value |
|---|---|---|
| 1 | "{quoted postcondition}" | {value bound, named in State table} |
| 2 | ... | ... |

**Step N.4 — invariant check** (optional, only if relevant invariants exist)

Cite the relevant `invariants.engspec § {name}` or function-level `### Invariants` section. State each invariant + its evaluation against post-frame state.

**Step N.5 — state update**

Name values added to the `## State` table in this frame.
```

**Rules:**

- **Every step cites or derives from a prior step.** If step N.3 says "insert blobs row", its citation must be the postcondition bullet that mandates the insert.
- **No step invents facts.** If the generator has to "assume" something not in a spec and not in the State table, it must flag that step with a `?` in a check column and propagate to `UNCLEAR`.
- **Branches must be disjoint.** If the spec has two branches for the same input (ambiguous), that's `UNCLEAR`, not a generator choice.
- **External calls are opaque.** For functions tagged `[external]` in the test engspec's Context, the frame records the call and its documented return value contract; the frame does not recurse into the external function's spec.

---

## `## Assertion evaluation`

One table per assertion code block in `## Subject`. Columns:

| Side | Expression | Resolved to | Derivation |
|------|-----------|-------------|-----------|
| LHS | {expression from assertion} | {value from State table} | {Frame N Step N.M reference} |
| RHS | {expected value from assertion} | {literal or State value} | {literal, or Frame N Step N.M} |
| Op | `{==, is, raises, <, ...}` | {True / False / Raised=X} | {equality rule applied} |

For assertions that expect an exception:

```markdown
| LHS | `resolve(doc, "/missing")` | Raises `KeyNotFound` | Frame 2 Step 2.1 ✗ → failure path |
| RHS | `KeyNotFound` | `KeyNotFound` | literal in `pytest.raises(...)` |
| Op  | `isinstance` | True | exception type match |
```

---

## `## Verdict: {PASS | FAIL | UNCLEAR}`

Exactly one verdict. The body shape depends on the verdict.

### PASS

```markdown
## Verdict: PASS
- Every cited postcondition was used; no uncited facts; no underdetermined steps.
- All assertion evaluations returned True.
```

### FAIL

```markdown
## Verdict: FAIL

**Root cause** — Frame {N} Step {N.M} derives {value X}, but assertion expects {value Y}.

**Spec reference** — `{impl_spec} § {function} § {section} bullet {n}` says: "{quote}"

**Resolution options**
1. {Fix the test: concrete proposal}
2. {Fix the impl spec: concrete proposal}

**Recommended** — {which option and why}
```

### UNCLEAR

```markdown
## Verdict: UNCLEAR

**Underdetermined step(s)**
- Frame {N} Step {N.M}: {what could not be derived}

**Gap location** — `{spec path} § {function or section}` {is missing | is ambiguous between X and Y | allows multiple outputs}.

**Why it matters** — {which other traces depend on this, if any}

**Suggested spec strengthening** — {concrete addition, ideally as a fenced code block ready to paste into the spec}
```

The generator MUST NOT emit `PASS` if any step is underdetermined, even if the assertion happens to hold under one plausible reading. Underdetermination → `UNCLEAR`.

---

## Citation format

Citations follow a strict grammar so the verifier can mechanically resolve them:

```
{spec-file-path}
{spec-file-path} § {function_name_or_file_level_section}
{spec-file-path} § {function_name} § {section_name}
{spec-file-path} § {function_name} § {section_name} bullet {n}
```

Examples:

- `nodes.engspec § write` — the whole function section
- `nodes.engspec § write § Preconditions` — just the Preconditions block
- `nodes.engspec § write § Failure Modes bullet 2` — the 2nd bullet of Failure Modes
- `tests/resolve.engspec § <file-level: fixtures>` — a file-level pseudo-function

The verifier's job per citation: open the file, locate the section, confirm the quoted or paraphrased content in the trace matches what the spec currently says. A mismatch marks the trace invalid, not stale — stale means a checksum on the cited engspec function has changed since the trace was written.

---

## Canonical form + checksum

Traces get checksummed the same way engspecs do. The checksum guarantees the verifier and the generator are looking at the same bytes.

**Excluded from the hash:**
- The `<!-- checksum: ... -->` and `<!-- traced_at: ... -->` metadata lines
- The entire `## Verification` section (added by the verifier after-the-fact)

**Included:** everything else.

**Canonical form for hashing:**

1. Remove `<!-- checksum: ... -->` and `<!-- traced_at: ... -->` lines.
2. Remove the `## Verification` section and everything under it (to end of file).
3. Normalize line endings to `\n`.
4. Strip trailing whitespace from each line (preserve leading whitespace).
5. Collapse runs of blank lines to a single blank line.
6. Encode as UTF-8.
7. Compute MD5 hex digest.

The generator writes the checksum into the header after emitting the body. The verifier recomputes and compares — a mismatch means the trace was edited after generation, and the verification proceeds with a `tampered: true` note in the verification block.

---

## `## Verification` — appended by the verifier

The verifier appends this section; the generator never writes it. Its presence does not invalidate the trace's checksum (it is excluded from the canonical form).

```markdown
## Verification

<!-- verified_by: {model identifier} -->
<!-- verified_at: {ISO 8601 timestamp} -->
<!-- verified_checksum: {MD5 of trace body at verification time} -->
<!-- result: {TRACE_VALID | TRACE_INVALID | TRACE_STALE} -->

### Checks performed
- Checksum match: {✓ | ✗, recomputed={...}, expected={...}}
- Citation validity: {N/N resolved | list of failures}
- State table consistency: {N/N references bound before use | list of dangling refs}
- Verdict consistency: {✓ | ✗ — verdict says {X} but evaluation table shows {Y}}

### Issues
- {list of specific issues, each pointing to a Frame + Step}
- {or: "none"}

### Result
- {TRACE_VALID: the trace's verdict is correctly derived from the current specs.}
- {TRACE_INVALID: at least one step does not follow from its citation. Regenerate the trace.}
- {TRACE_STALE: the trace was valid when written, but at least one cited engspec has changed since. Regenerate the trace.}
```

A `TRACE_VALID` verdict is a signed proof that the test engspec + impl engspecs, as they exist now, entail the trace's PASS/FAIL/UNCLEAR conclusion. It is not a claim about any implementation's correctness.

---

## Worked example: PASS

```markdown
<!-- engspec-trace v1 -->
<!-- test_spec: tests/resolve.engspec -->
<!-- test_function: test_root_pointer -->
<!-- impl_specs: src/resolve.engspec -->
<!-- traced_by: claude-opus-4-7 -->
<!-- traced_at: 2026-04-19T14:00:00Z -->
<!-- verdict: PASS -->
<!-- checksum: 4a8b2c1d3e5f6789abcdef0123456789 -->

## Subject

```python
assert resolve({"foo": ["bar", "baz"]}, "") is doc
```

## Given
- `doc = {"foo": ["bar", "baz"]}` — from tests/resolve.engspec § test_root_pointer § Preconditions.

## State

| Name | Bound in | Value / description |
|---|---|---|
| `doc` | Given | `{"foo": ["bar", "baz"]}` |
| `tokens` | Frame 1 Step 1.3 | `[]` — empty list |
| `result` | Frame 2 Step 2.2 | `doc` itself (identity, not equality) |

## Trace

### Frame 1: parse("")

**Call** — `parse(pointer="")`
**Cite** — `src/resolve.engspec § parse`

**Step 1.1 — precondition check**

| # | Bullet | Check | ✓ |
|---|---|---|---|
| 1 | "pointer is a string" | `""` is a str | ✓ |

**Step 1.2 — branch selection**

Cite `src/resolve.engspec § parse § Implementation Notes`: "if pointer is empty string, return []; otherwise split on '/' after the leading '/' is consumed". Input `""` takes the empty-string branch.

**Step 1.3 — postcondition application**

| # | Postcondition | Resolved |
|---|---|---|
| 1 | "returns list of reference tokens" | bind `tokens = []` |
| 2 | "empty string → empty list" | consistent with bound value |

### Frame 2: resolve(doc, "")

**Call** — `resolve(document=doc, pointer="")`
**Cite** — `src/resolve.engspec § resolve`

**Step 2.1 — precondition check**

| # | Bullet | Check | ✓ |
|---|---|---|---|
| 1 | "document is JSON value" | `doc` is a dict | ✓ |
| 2 | "pointer is a string" | `""` is a str | ✓ |

**Step 2.2 — postcondition application**

| # | Postcondition | Resolved |
|---|---|---|
| 1 | "if parse(pointer) is empty, return document unchanged" | bind `result = doc` (identity) |

## Assertion evaluation

| Side | Expression | Resolved to | Derivation |
|------|-----------|-------------|-----------|
| LHS | `resolve(doc, "")` | `doc` | Frame 2 Step 2.2 |
| RHS | `doc` | `doc` | literal in test |
| Op  | `is` | True | identity preserved per Postcondition 1 |

## Verdict: PASS
- Every cited postcondition was used; no uncited facts; no underdetermined steps.
- Assertion evaluation returned True.
```

---

## Worked example: UNCLEAR

```markdown
...
## Verdict: UNCLEAR

**Underdetermined step**
- Frame 2 Step 2.2: Postcondition 1 says "returns the referenced element" but src/resolve.engspec § resolve does not define the semantics of array index `-` (end-of-array per RFC 6901 §4) and does not document whether that index is accepted for read vs. write.

**Gap location** — `src/resolve.engspec § resolve § Postconditions` does not mention `-`.

**Why it matters** — `tests/resolve.engspec § test_dash_on_read` and `§ test_dash_on_write` both depend on this. Both are UNCLEAR until resolved.

**Suggested spec strengthening** — add to `src/resolve.engspec § resolve § Postconditions`:

    - Array token "-" on read: raises IndexOutOfBounds (refers to a nonexistent
      element past the array end, per RFC 6901 §4).
    - Array token "-" on write: refers to the one-past-end insertion point
      (JSON Patch semantics, out of scope for read-only resolve — reject).
```

---

## When a trace is not the right answer

Some properties cannot be traced cheaply. For these, the test engspec should either mock the behavior or mark the test `trace: skipped`:

- Behaviors that depend on **randomness** (e.g., "returns a uuid"). Trace can assert "returns a string of length 36 matching uuid pattern" but not the specific value.
- Behaviors that depend on **wall-clock time** beyond monotonic ordering. The test should fix the clock in a fixture and reference it from the trace.
- Behaviors that require **BM25, ML model output, or other opaque scoring** — trace can confirm "returns non-empty list sorted by score descending" but not the ranking itself.
- **Large state spaces** — property tests over random sequences of ops. The trace should walk a representative sequence and the test assertion should be invariant-style, not value-specific.
- **Syscall / kernel behavior** — trace accepts the spec's abstraction as axiomatic. This is the same assumption a mocked unit test makes.

When a test is `trace: skipped`, the pipeline still runs regeneration + actual-test-execution; the trace step is just bypassed for that test. The pipeline's success criterion is "every traceable test traces PASS AND every generated test passes the generated code," not "every test has a PASS trace."

---

## How this plugs into the engspec pipeline

```
engspec_prompt.md           →  code → engspec (with 3/3 regeneration)
engspec_trace_prompt.md     →  (test + impl specs) → trace (PASS/FAIL/UNCLEAR)
engspec_verify_trace_prompt.md → trace → TRACE_VALID/INVALID/STALE
engspec_tester_prompt.md    →  adversarial debate (strengthens specs)
engspec_to_code_prompt.md   →  engspec → code (regenerates, runs tests)
```

Tracing runs **before** adversarial debate. A trace that converges to UNCLEAR finds the cheapest spec gaps — before debate, before regeneration, before any code. Only after every traceable test traces PASS does it become worth spending debate rounds on the specs.
