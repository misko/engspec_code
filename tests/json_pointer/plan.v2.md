# Plan v2: JSON Pointer (RFC 6901) resolver

*Stage 3 output — revised after writing the test engspec in Stage 2. See `plan.md` for the original.*

## Changes from v1

Writing 25 concrete test functions surfaced four things the original plan did not name.

### 1. `PointerError` base class needs a direct test

v1 listed the five exception classes but treated `PointerError` as an internal grouping device. Writing the tests made clear that `PointerError` is part of the *public contract* — consumers will write `except PointerError:` to catch any resolve failure, and that catch behavior must be spec'd and tested. Added `test_pointer_error_is_base_class` which exercises all four subclasses through the base.

**Impact on impl engspec:** `PointerError` gets its own `##` section (not just a class header), with a Postcondition that all four subclasses inherit from it.

### 2. Negative-index test is distinct from leading-zero test

v1's "bad index format" bullet lumped together `01`, `-1`, `1.0`, `+1`. Writing the tests showed that `/a/-1` is a meaningfully different case from `/a/01`:

- `-1` is a Python-idiomatic negative index, and a reasonable developer might expect it to work.
- `01` is just wrong syntax.

Both raise `PointerSyntaxError`, but the explicit negative-index test anchors the negative boundary: we do NOT adopt Python-style negative indexing. Added `test_syntax_error_negative_index`.

**Impact on impl engspec:** `_resolve_token` Failure Modes must explicitly list `-{digits}` as PointerSyntaxError, separately from the leading-zero case. The regex `^(0|[1-9][0-9]*)$` covers both implicitly, but naming the negative case in prose prevents "I'll add a special case for negative" drift.

### 3. Fixture location is a real decision

v1 did not discuss where the `rfc_doc` fixture lives. Writing the test engspec forced the question: inline `<file-level: imports>` vs. a separate `conftest.py.engspec`. Chose inline — the fixture is specific to these tests, and a conftest buys nothing when there's only one test file.

**Impact on impl engspec:** none. But `engspec_to_code_prompt.md` regeneration will correctly produce a test file with the fixture at top, not a conftest.

### 4. Empty-key test needs identity semantics too

v1 said `resolve(doc, "")` returns identity. v2 adds: `resolve(None, "")` returns `None` *by identity* (`is None`, which is true for any Python `None` reference, but still worth making explicit in the Postcondition). Added `test_resolve_none_with_empty_pointer`.

**Impact on impl engspec:** `resolve` Postcondition 1 becomes "returns `document` unchanged (same object, via `is`) when the pointer is empty" — the "same object" clause was there in v1, this just confirms it for the None case.

## Unchanged

The module layout, function signatures, type boundaries, and all other decisions from v1 stand. In particular:

- Two files (`resolve.py`, `exceptions.py`) plus `__init__.py`.
- Functions `resolve` (public) and `_parse`, `_unescape`, `_resolve_token` (internal).
- Five exception classes with dual inheritance (library + stdlib).
- Escape order `~1` before `~0`.
- Identity on empty pointer.
- Dash `-` always `IndexOutOfBounds` on read.

## Ambiguities resolved during Stage 2

- **Confirming ambiguity #1 from v1** (dual inheritance): going with dual inheritance. Tests use `except PointerSyntaxError`, `except KeyNotFound`, etc. — which would work either way — but `test_pointer_error_is_base_class` pins the group-catch behavior that dual inheritance doesn't give you for free (you'd need to catch `(KeyError, IndexError, TypeError, ValueError)` without it).
- **Confirming ambiguity #5 from v1** (trailing slash on list): not tested in this v2 — the RFC does not specify it, and our escape-order anti-regression tests already exercise the interesting corner. Leaving `/foo/` behavior as an explicit gap in the impl engspec's Implementation Notes: `_resolve_token` will treat empty token on a list as `PointerSyntaxError` because empty string doesn't match the index regex. If a test emerges that depends on this, we'll revisit.

## What Stage 4 (impl engspec) must satisfy

Every assertion in the test engspec maps to a Postcondition or Failure Mode in the impl engspec. The mapping:

| Test function                                | Impl spec obligation |
|----------------------------------------------|----------------------|
| `test_empty_pointer_returns_document`        | `resolve` Postcondition: empty pointer → identity of document |
| `test_*` (10 RFC §5 vectors)                 | `resolve` Postcondition: folding `_resolve_token` over `_parse(pointer)` yields referenced value; `_unescape` Postcondition for escaped keys |
| `test_escape_order_tilde_one_first`, `..._slash_key` | `_unescape` Implementation Notes: `~1 → /` applied before `~0 → ~` |
| `test_syntax_error_no_leading_slash`         | `_parse` Failure Mode: non-empty pointer lacking leading `/` raises `PointerSyntaxError` |
| `test_syntax_error_trailing_tilde`           | `_parse` Failure Mode: trailing `~` raises `PointerSyntaxError` |
| `test_syntax_error_bad_escape`               | `_parse` Failure Mode: `~` not followed by `0` or `1` raises `PointerSyntaxError` |
| `test_syntax_error_leading_zero_index`       | `_resolve_token` Failure Mode: invalid index format raises `PointerSyntaxError` |
| `test_syntax_error_negative_index`           | same as above; named explicitly in Implementation Notes |
| `test_key_not_found`                         | `_resolve_token` Failure Mode: dict missing key raises `KeyNotFound` |
| `test_index_out_of_bounds`                   | `_resolve_token` Failure Mode: list index ≥ len raises `IndexOutOfBounds` |
| `test_dash_index_rejected`                   | `_resolve_token` Failure Mode: token `-` on list raises `IndexOutOfBounds` |
| `test_type_mismatch_scalar`                  | `_resolve_token` Failure Mode: descent into non-container raises `TypeMismatch` |
| `test_resolve_none_with_empty_pointer`       | Covered by the identity Postcondition on `resolve` |
| `test_pointer_error_is_base_class`           | `exceptions.py` `<file-level: class hierarchy>`: all four specific classes inherit from `PointerError` |

The impl engspec will be complete when every row above has a named citation. Any row without one is a Stage 4 gap.

## Ready-to-proceed checklist

- [x] Test engspec written (Stage 2).
- [x] All 25 test functions have verbatim assertion code blocks.
- [x] Coverage table above shows each test's impl-spec obligation.
- [ ] Stage 4: write impl engspec with sections addressing every obligation.
