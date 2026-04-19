# engspec-verify-trace: Check a Trace

Use this document as instructions to verify an existing `.trace.md` file. You will not re-derive the trace — you will check that each of its steps is locally sound given the cited engspecs, then append a `## Verification` section with a ruling of **TRACE_VALID**, **TRACE_INVALID**, or **TRACE_STALE**.

The trace format — section order, citation grammar, state-table rules, canonical checksum — is defined in `engspec_trace_format.md`. Read it before proceeding.

---

## How to use this

```
Read /path/to/engspec_verify_trace_prompt.md for your instructions.
Read /path/to/engspec_trace_format.md for the trace format.

Trace file: /path/to/tests/some_test.engspec/traces/test_some_behavior.trace.md

Please verify this trace.
```

If the user passes a directory, verify every `*.trace.md` under it and emit a summary.

---

## Why verification is distinct from generation

A generator re-derives every step; a verifier checks that each step is locally sound. Proof-checking is strictly easier than proof-finding, and having a separate agent perform it means the human-facing **TRACE_VALID** verdict is produced by someone who hasn't already committed to an answer. Do not recompute any postcondition application; only check that the trace's claims are consistent with its citations.

---

## Phase 1: Load

1. **Read the trace file.** Note `verdict`, `test_spec`, `test_function`, `impl_specs`, `traced_at`, `checksum`.
2. **Read the test engspec** and locate the `##` section named in `test_function`.
3. **Read every impl engspec** named in `impl_specs` plus any `conftest.engspec` co-located with the test spec.
4. **Snapshot the checksums** of every cited impl-engspec function section, and the `source_commit` of each file.

---

## Phase 2: Check the cheap things first

Run these in order; stop and append `TRACE_INVALID` or `TRACE_STALE` as soon as one fails.

### 2.1 Checksum integrity

Recompute the trace's canonical checksum per `engspec_trace_format.md § Canonical form + checksum`. Compare to the header. If they differ, the trace was edited after generation — record as `tampered: true` in the verification block, continue verifying, and include the mismatch in `### Issues`. Do not stop: an edited trace can still be checked.

### 2.2 Staleness

For each cited impl-engspec function section, check its current `<!-- checksum: ... -->`:

- If it matches what was in the spec at `traced_at` (verifiable via git if the spec is in a repo, or by comparison to the versions loaded in Phase 1 assuming they haven't moved): proceed.
- If any cited function's checksum has changed since `traced_at`, the trace is **stale**. Emit `TRACE_STALE` with the list of changed functions and stop.

The staleness check is not invalidation — stale traces were correct when written. They need regeneration, not fixing.

### 2.3 Structural well-formedness

Confirm the trace has every required section in the prescribed order. Missing or out-of-order sections are `TRACE_INVALID` with a specific issue noted.

---

## Phase 3: Check citations

For every citation in the trace (Frame step tables, Given, Assertion evaluation):

- Parse the citation per the grammar in `engspec_trace_format.md § Citation format`.
- Open the cited spec file; locate the section.
- If the citation references a specific bullet (`bullet N`), confirm the Nth bullet exists.
- If the trace quotes content in the check/postcondition column, confirm the quote appears in that section (exact substring match, allowing minor whitespace differences).
- Record per-citation ✓/✗. Any ✗ is a trace error, not a staleness.

Short-circuit rule: if more than 20% of citations fail to resolve, stop checking further and rule `TRACE_INVALID` — the trace is plausibly writing about a different version of the specs.

---

## Phase 4: Check state-table consistency

For every State table entry, note its `Bound in` step. For every name referenced in a Frame step or the Assertion evaluation, confirm:

- The name appears in the State table.
- Its `Bound in` step is strictly earlier than the referring step.

A dangling reference (named but not in the State table) is `TRACE_INVALID`. A forward reference (bound later than used) is `TRACE_INVALID`.

---

## Phase 5: Check verdict consistency

Open `## Assertion evaluation`. Compute the verdict that the evaluation table implies:

- If every row's Op column says `True` or equivalent (match on raised exception, identity holds, etc.): implied verdict is `PASS`.
- If every step is derivable (no `?`) AND at least one row is `False`: implied verdict is `FAIL`.
- If any Frame step has a `?` or an UNCLEAR-triggering flag: implied verdict is `UNCLEAR`.

Compare to `<!-- verdict: ... -->` in the header. A mismatch is `TRACE_INVALID`.

---

## Phase 6: Check that the Failure/UNCLEAR body matches the evidence

If verdict is **FAIL**:
- The Root cause must name a specific Frame N Step N.M.
- The Spec reference must be a well-formed citation that resolves.
- At least two Resolution options must be listed.
- The Recommended line must pick one.

If verdict is **UNCLEAR**:
- At least one Underdetermined step must be named.
- Gap location must be a well-formed citation.
- Suggested spec strengthening must be concrete — prose like "clarify this" without a proposed addition is a partial issue.

Partial compliance here is noted as an issue but does not in itself make the trace `TRACE_INVALID` — it's a quality concern, not a soundness concern.

---

## Phase 7: Append the verification block

Append the section to the trace file. Do not modify any other section. The verification section is excluded from the trace's checksum by design, so re-running the verifier does not invalidate the trace.

```markdown
## Verification

<!-- verified_by: claude-opus-4-7 -->
<!-- verified_at: 2026-04-19T14:30:00Z -->
<!-- verified_checksum: {recomputed MD5} -->
<!-- result: {TRACE_VALID | TRACE_INVALID | TRACE_STALE} -->

### Checks performed
- Checksum match: {✓ | ✗ (recomputed vs. header)}
- Staleness: {✓ | list of changed functions}
- Structural well-formedness: {✓ | list of missing/misordered sections}
- Citation validity: {N/N resolved | list of failed citations with Frame/Step}
- State table consistency: {N/N references bound before use | list of issues}
- Verdict consistency: {✓ | implied X, trace says Y}
- Verdict body quality: {✓ | list of partial-compliance notes}

### Issues
- {per-issue bullet: location + what's wrong + severity}
- {or: "none"}

### Result
- {one-sentence ruling with specific reasoning}
```

Do NOT regenerate the trace or edit any section before `## Verification`. If the trace is invalid, report what's wrong — regenerating is the generator's job.

---

## Summary mode

If the user passed a directory or `--all`, emit a summary to the terminal:

```
VERIFY SUMMARY for tests/resolve.engspec/traces/:
  test_root_pointer.trace.md           TRACE_VALID
  test_single_key.trace.md             TRACE_VALID
  test_escape_tilde.trace.md           TRACE_INVALID (Frame 2 Step 2.3 cites bullet 4, Postconditions has 3 bullets)
  test_array_index.trace.md            TRACE_STALE (src/resolve.engspec § resolve checksum changed)

Valid: 2 | Invalid: 1 | Stale: 1
```

---

## Principles

1. **Proof-check, don't re-derive.** The verifier's job is cheaper than the generator's. Checking a step is "does the cited bullet support the claim?" — not "what does the bullet imply?"
2. **Local soundness, not correctness.** A trace can be VALID even if it arrives at a wrong answer, as long as every step follows from its citation. The wrongness belongs to the specs, not the trace.
3. **Stale ≠ invalid.** A stale trace was valid when written; specs changed. Regeneration is the fix, not spec work.
4. **Don't trust the verdict header alone.** Compute the implied verdict from the evaluation table and compare.
5. **Be forgiving about whitespace, strict about substance.** Quote mismatches on whitespace are not issues; quote mismatches on content are.
6. **One-shot.** Verification is not iterative. Read, check, append, done.

---

## Operational requirements

Use the most capable available model. In Claude Code, pass `model: "opus"` for any subagent invocations. The verifier is cheaper than the generator, but is still doing careful spec reading — do not downgrade to Haiku/Sonnet.
