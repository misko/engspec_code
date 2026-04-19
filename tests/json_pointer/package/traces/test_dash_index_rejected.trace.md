<!-- engspec-trace v1 -->
<!-- test_spec: specs/tests/test_resolve.py.engspec -->
<!-- test_function: test_dash_index_rejected -->
<!-- impl_specs: specs/src/resolve.py.engspec -->
<!-- traced_by: claude-opus-4-7 -->
<!-- traced_at: 2026-04-19T09:32:00Z -->
<!-- verdict: PASS -->
<!-- checksum: placeholder-trace-3 -->

## Subject

```python
with pytest.raises(IndexOutOfBounds):
    resolve({"a": [1, 2]}, "/a/-")
```

## Given
- `doc = {"a": [1, 2]}` — built inline in the test.
- `pointer = "/a/-"` — literal in the test.

## State

| Name | Bound in | Value / description |
|---|---|---|
| `doc` | Given | `{"a": [1, 2]}` |
| `tokens` | Frame 2 Step 2.4 | `["a", "-"]` — two tokens, neither escaped |
| `current_after_a` | Frame 3 Step 3.3 | `[1, 2]` — the list at `doc["a"]` (same object as `doc["a"]`) |
| `raised` | Frame 4 Step 4.1a | `IndexOutOfBounds("token '-' refers to the one-past-end element; not valid for read")` |

## Trace

### Frame 1: resolve(doc, "/a/-")

**Call** — `resolve(document=doc, pointer="/a/-")`
**Cite** — `specs/src/resolve.py.engspec § resolve`

**Step 1.1 — precondition check**

| # | Bullet | Check | ✓ |
|---|---|---|---|
| 1 | "document is a JSON value" | `doc` is a `dict` | ✓ |
| 2 | "pointer is a str" | `"/a/-"` is a `str` | ✓ |

**Step 1.2 — branch selection**

Non-empty pointer → fold branch per Postcondition 2.

### Frame 2: _parse("/a/-")

**Call** — `_parse(pointer="/a/-")`
**Cite** — `specs/src/resolve.py.engspec § _parse`

**Step 2.1 — precondition check**

| # | Bullet | Check | ✓ |
|---|---|---|---|
| 1 | "pointer is a str" | `"/a/-"` is a `str` | ✓ |

**Step 2.2 — branch selection**

Non-empty, starts with `/` → split branch.

**Step 2.3 — postcondition application**

- Consume leading `/`: remainder `"a/-"`.
- Split on `/`: `["a", "-"]`.
- `_validate_escapes("a")`: no `~`, returns `"a"`.
- `_unescape("a")`: no replacements possible, returns `"a"`.
- `_validate_escapes("-")`: no `~`, returns `"-"`.
- `_unescape("-")`: no replacements, returns `"-"`.

**Step 2.4 — bind result**

`tokens = ["a", "-"]`.

### Frame 3: _resolve_token(doc, "a")

**Call** — `_resolve_token(value=doc, token="a")`
**Cite** — `specs/src/resolve.py.engspec § _resolve_token`

**Step 3.1 — precondition check**

| # | Bullet | Check | ✓ |
|---|---|---|---|
| 1 | "value is a JSON value" | `doc` is a `dict` | ✓ |
| 2 | "token is a str" | `"a"` is a `str` | ✓ |

**Step 3.2 — branch selection**

`isinstance(value, dict)` → True. Dict branch.

**Step 3.3 — postcondition application**

Per Postconditions bullet 1: "If `value` is a `dict` and `token` is a key in `value`, returns `value[token]`."

`"a"` is a key in `doc` ✓. Return `doc["a"]` = `[1, 2]`.

Bind `current_after_a = [1, 2]`.

### Frame 4: _resolve_token([1, 2], "-")

**Call** — `_resolve_token(value=[1, 2], token="-")`
**Cite** — `specs/src/resolve.py.engspec § _resolve_token`

**Step 4.1 — precondition check**

| # | Bullet | Check | ✓ |
|---|---|---|---|
| 1 | "value is a JSON value" | `[1, 2]` is a `list` | ✓ |
| 2 | "token is a str" | `"-"` is a `str` | ✓ |

**Step 4.2 — branch selection**

`isinstance(value, list)` → True. List branch.

Cite `specs/src/resolve.py.engspec § _resolve_token § Implementation Notes`:
"Check order matters for lists: `-` must be checked BEFORE the regex, because `-` would fail the regex and we want `IndexOutOfBounds`, not `PointerSyntaxError`, for the dash."

Input token is `"-"` → take the dash-specific sub-branch.

**Step 4.1a — failure mode**

Cite `specs/src/resolve.py.engspec § _resolve_token § Failure Modes bullet 2`:
"If `value` is a `list` and `token == "-"`: raises `IndexOutOfBounds`. **propagated**."

Input matches this condition exactly. Frame raises `IndexOutOfBounds`. No further frames run.

Bind `raised = IndexOutOfBounds`.

### Frame 1 (continuation): propagation

Cite `specs/src/resolve.py.engspec § resolve § Failure Modes`: "All `_resolve_token` failure modes: **propagated**." `resolve` re-raises the `IndexOutOfBounds` from Frame 4 to the test.

## Assertion evaluation

The test uses `pytest.raises(IndexOutOfBounds)` as a context manager. The assertion semantics: the body must raise an exception that is an instance of `IndexOutOfBounds`.

| Side | Expression | Resolved to | Derivation |
|------|-----------|-------------|-----------|
| LHS | `resolve({"a": [1, 2]}, "/a/-")` | Raises `IndexOutOfBounds` | Frame 4 Step 4.1a → Frame 1 propagation |
| RHS | `IndexOutOfBounds` | `IndexOutOfBounds` class | literal in `pytest.raises(...)` |
| Op  | `isinstance(raised, RHS)` | True | exact class match |

## Verdict: PASS

- The dash-rejection behavior is explicitly mandated by `_resolve_token § Failure Modes bullet 2`.
- The check order (dash before regex) is explicitly mandated by `_resolve_token § Implementation Notes`.
- The propagation through `resolve` is explicitly mandated by `resolve § Failure Modes`.
- Every step cited a specific bullet. No alternative spec reading would derive a different exception class.

## Verification

<!-- verified_by: claude-opus-4-7 -->
<!-- verified_at: 2026-04-19T09:42:00Z -->
<!-- verified_checksum: placeholder-verify-3 -->
<!-- result: TRACE_VALID -->

### Checks performed
- Checksum match: placeholder (smoke test).
- Staleness: ✓.
- Structural well-formedness: ✓.
- Citation validity: 7/7 resolved.
  - `specs/src/resolve.py.engspec § resolve` — present.
  - `specs/src/resolve.py.engspec § resolve § Failure Modes` — present; includes "All `_resolve_token` failure modes: **propagated**."
  - `specs/src/resolve.py.engspec § _parse` — present.
  - `specs/src/resolve.py.engspec § _resolve_token` — present.
  - `specs/src/resolve.py.engspec § _resolve_token § Failure Modes bullet 2` — present: "If `value` is a `list` and `token == "-"`: raises `IndexOutOfBounds`. **propagated**." Matches the trace's quotation.
  - `specs/src/resolve.py.engspec § _resolve_token § Implementation Notes` — present; the "Check order matters for lists: `-` must be checked BEFORE the regex" clause matches the trace's quotation verbatim.
  - `specs/src/resolve.py.engspec § _resolve_token § Postconditions bullet 1` (for Frame 3) — present.
- State table consistency: 4/4 references bound before use.
  - `doc` bound in Given; referenced Frame 1, 3 ✓.
  - `tokens` bound Frame 2 Step 2.4; referenced in Frame 1's loop ✓.
  - `current_after_a` bound Frame 3 Step 3.3; referenced Frame 4 as `value` ✓.
  - `raised` bound Frame 4 Step 4.1a; referenced in Assertion ✓.
- Verdict consistency: ✓ — `pytest.raises(IndexOutOfBounds)` assertion; isinstance check returned True; verdict PASS.
- Verdict body quality: ✓.

### Issues
- none

### Result
- **TRACE_VALID**: the trace's PASS verdict is correctly derived. Every exception-class choice and check-order decision cites a specific spec bullet. The propagation through `resolve` is explicit in the cited Failure Modes section.
