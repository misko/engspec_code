<!-- engspec-trace v1 -->
<!-- test_spec: specs/tests/test_resolve.py.engspec -->
<!-- test_function: test_escape_order_tilde_one_first -->
<!-- impl_specs: specs/src/resolve.py.engspec -->
<!-- traced_by: claude-opus-4-7 -->
<!-- traced_at: 2026-04-19T09:31:00Z -->
<!-- verdict: PASS -->
<!-- checksum: placeholder-trace-2 -->

## Subject

```python
assert resolve({"~1": "kept-as-tilde-one"}, "/~01") == "kept-as-tilde-one"
```

## Given
- `doc = {"~1": "kept-as-tilde-one"}` — built inline in the test, not via fixture.
  Cite: literal in the test's Postcondition code block.
- `pointer = "/~01"` — literal in the test.

## State

| Name | Bound in | Value / description |
|---|---|---|
| `doc` | Given | `{"~1": "kept-as-tilde-one"}` — one-element dict with the two-character string `~1` as its only key |
| `tokens` | Frame 2 Step 2.4 | `["~1"]` — a list with one string of length 2 (tilde, one) |
| `decoded_token` | Frame 3 Step 3.3 | `"~1"` — the string (tilde, one), returned by `_unescape("~01")` |
| `result` | Frame 4 Step 4.3 | `"kept-as-tilde-one"` — `doc["~1"]` |

## Trace

### Frame 1: resolve(doc, "/~01")

**Call** — `resolve(document=doc, pointer="/~01")`
**Cite** — `specs/src/resolve.py.engspec § resolve`

**Step 1.1 — precondition check**

| # | Bullet | Check | ✓ |
|---|---|---|---|
| 1 | "document is a JSON value" | `doc` is a `dict` | ✓ |
| 2 | "pointer is a str" | `"/~01"` is a `str` | ✓ |

**Step 1.2 — branch selection**

Cite `specs/src/resolve.py.engspec § resolve § Postconditions` bullet 2 + Implementation Notes: `pointer != ""` selects the fold branch — call `_parse(pointer)`, iterate over tokens, apply `_resolve_token`.

**Step 1.3 — delegates to _parse then _resolve_token (see Frames 2-4)**

### Frame 2: _parse("/~01")

**Call** — `_parse(pointer="/~01")`
**Cite** — `specs/src/resolve.py.engspec § _parse`

**Step 2.1 — precondition check**

| # | Bullet | Check | ✓ |
|---|---|---|---|
| 1 | "pointer is a str" | `"/~01"` is a `str` | ✓ |

**Step 2.2 — branch selection**

Cite `specs/src/resolve.py.engspec § _parse § Postconditions`:
- Bullet 1 applies if `pointer == ""`. Input is `"/~01"`, not empty → skip.
- Bullet 2 applies if pointer starts with `/`. Input does → select split branch.

**Step 2.3 — postcondition application**

Per Postcondition 2:
- Consume leading `/`: remainder `"~01"`.
- Split on `/`: `["~01"]` (no further `/` characters).
- Apply `_validate_escapes` to each token: validates `~` is followed by `0` or `1`.
  - Token `"~01"`: at index 0 is `~`, at index 1 is `0` ∈ {`0`, `1`} ✓. Continue. Index 2 is `1`, not `~`. End of string. No violation. Return `"~01"` unchanged.
- Apply `_unescape` to each token: see Frame 3.

**Step 2.4 — bind result**

After `_unescape` (Frame 3) returns `"~1"`: bind `tokens = ["~1"]`.

### Frame 3: _unescape("~01")

**Call** — `_unescape(token="~01")`
**Cite** — `specs/src/resolve.py.engspec § _unescape`

**Step 3.1 — precondition check**

| # | Bullet | Check | ✓ |
|---|---|---|---|
| 1 | "token is a str" | `"~01"` is a `str` | ✓ |
| 2 | "token is well-formed per `_parse`'s `_validate_escapes` — every `~` is followed by `0` or `1`" | validated in Frame 2 Step 2.3 | ✓ |

**Step 3.2 — postcondition application**

Cite `specs/src/resolve.py.engspec § _unescape § Postconditions` bullet 1:

```python
token.replace("~1", "/").replace("~0", "~")
```

Applied to `"~01"`:

1. First pass — `"~01".replace("~1", "/")`:
   Python's `str.replace` scans left-to-right for non-overlapping occurrences of the search substring.
   In `"~01"`, the substring `"~1"` would require adjacent `~` and `1`. Character positions: pos 0 is `~`, pos 1 is `0`, pos 2 is `1`. At pos 0 the pair is `~0` (not `~1`). At pos 1 the pair is `01` (not `~1`). No match. Result: `"~01"` (unchanged).

2. Second pass — `"~01".replace("~0", "~")`:
   Looking for `~0`. At pos 0, pair is `~0` ✓ — match. Replace `~0` (2 chars) with `~` (1 char). Result: `"~1"` (tilde followed by `1`).

Per Postcondition bullet 2: "Order is critical: `~1` is replaced FIRST, then `~0` is replaced. This correctly handles the token `~01` — under the correct order it decodes to `~1` (literal tilde + `1`); under the reverse order it would corrupt to `/`."

**Step 3.3 — bind result**

Bind `decoded_token = "~1"` (tilde, one).

### Frame 4: _resolve_token(doc, "~1")

**Call** — `_resolve_token(value=doc, token="~1")`
**Cite** — `specs/src/resolve.py.engspec § _resolve_token`

**Step 4.1 — precondition check**

| # | Bullet | Check | ✓ |
|---|---|---|---|
| 1 | "`value` is a JSON value" | `doc` is a `dict` | ✓ |
| 2 | "`token` is a decoded reference token (any string, possibly empty)" | `"~1"` is a `str` | ✓ |

**Step 4.2 — branch selection**

Cite `specs/src/resolve.py.engspec § _resolve_token § Implementation Notes` — order of type checks:
- `isinstance(value, dict)` → True. Take the dict branch. (Do not reach list branch or TypeMismatch branch.)

**Step 4.3 — postcondition application**

Cite `specs/src/resolve.py.engspec § _resolve_token § Postconditions` bullet 1: "If `value` is a `dict` and `token` is a key in `value`, returns `value[token]`."

Check: is `"~1"` in `doc`? `doc = {"~1": "kept-as-tilde-one"}` — yes, `"~1"` is its only key.

Return `doc["~1"]` = `"kept-as-tilde-one"`.

Bind `result = "kept-as-tilde-one"`.

## Assertion evaluation

| Side | Expression | Resolved to | Derivation |
|------|-----------|-------------|-----------|
| LHS | `resolve({"~1": "kept-as-tilde-one"}, "/~01")` | `"kept-as-tilde-one"` | Frame 4 Step 4.3 (identity propagated through Frame 1's loop return) |
| RHS | `"kept-as-tilde-one"` | `"kept-as-tilde-one"` | literal in test |
| Op  | `==` | True | string equality on equal literals |

## Verdict: PASS

- The escape-order behavior is derivable directly from `_unescape` § Postconditions bullet 1 (`.replace("~1", "/").replace("~0", "~")`) and bullet 2 (order-critical note).
- Every step cited a specific bullet; no assumptions inserted.
- This is the critical anti-regression: under reversed escape order the trace would derive `"/"` as the decoded token, lookup would fail with `KeyNotFound`, and the assertion would fail. The spec explicitly forbids that ordering via the fenced code block in Postcondition 1 and the note in bullet 2.

## Verification

<!-- verified_by: claude-opus-4-7 -->
<!-- verified_at: 2026-04-19T09:41:00Z -->
<!-- verified_checksum: placeholder-verify-2 -->
<!-- result: TRACE_VALID -->

### Checks performed
- Checksum match: placeholder (smoke test).
- Staleness: ✓ — impl engspec unchanged since trace generation.
- Structural well-formedness: ✓ — all sections present and ordered correctly.
- Citation validity: 8/8 resolved.
  - `specs/src/resolve.py.engspec § resolve` — present.
  - `specs/src/resolve.py.engspec § resolve § Postconditions` bullet 2 — present, matches quoted "returns the element obtained by folding …".
  - `specs/src/resolve.py.engspec § _parse` — present.
  - `specs/src/resolve.py.engspec § _parse § Postconditions` — present; the split-and-unescape behavior described in the trace matches bullet 2.
  - `specs/src/resolve.py.engspec § _unescape` — present.
  - `specs/src/resolve.py.engspec § _unescape § Postconditions` bullet 1 — present; the trace quotes the fenced code block `token.replace("~1", "/").replace("~0", "~")` verbatim.
  - `specs/src/resolve.py.engspec § _unescape § Postconditions` bullet 2 — present; the order-critical note matches.
  - `specs/src/resolve.py.engspec § _resolve_token § Postconditions` bullet 1 — present.
  - `specs/src/resolve.py.engspec § _resolve_token § Implementation Notes` — present; the type-check order described matches.
- State table consistency: 4/4 references bound before use.
  - `doc` bound in Given; referenced in Frame 1, 4 ✓.
  - `tokens` bound in Frame 2 Step 2.4; referenced in Frame 1's loop (conceptually, to enter Frame 4) after Step 2.4 ✓.
  - `decoded_token` bound in Frame 3 Step 3.3; this is the value of `tokens[0]` — referenced conceptually in Frame 4's invocation. ✓
  - `result` bound in Frame 4 Step 4.3; referenced in Assertion LHS ✓.
- Verdict consistency: ✓ — assertion Op `==` = True; no underdetermined steps; verdict PASS matches.
- Verdict body quality: ✓ — PASS body cites specific bullets and explicitly addresses the anti-regression property.

### Issues
- **Minor** (non-blocking): the trace relies on Python `str.replace` semantics in Step 3.2 (non-overlapping left-to-right scan). This is a language-level fact not in the impl engspec. It is defensible as common knowledge for a Python implementation, but strictly speaking the impl engspec could strengthen `_unescape § Postconditions` to name this dependence. Recorded for methodology follow-up; not a ruling change.

### Result
- **TRACE_VALID**: the trace's PASS verdict follows from cited spec sections. The escape-order derivation in Frame 3 is explicitly supported by both Postcondition bullets of `_unescape`.
