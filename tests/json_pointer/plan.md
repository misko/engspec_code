# Plan: JSON Pointer (RFC 6901) resolver

*Stage 1 output — derived from `idea.md`. Review and amend before Stage 2.*

## Module layout

One small Python package. All logic in one file; exceptions in their own file only because that file is imported for `isinstance` checks and keeping it separate makes those imports cheap.

```
src/json_pointer/
├── __init__.py         # re-exports `resolve` + all exception classes
├── resolve.py          # parse, unescape, resolve_token, resolve
└── exceptions.py       # PointerError + 4 subclasses
```

Public API (re-exported from `__init__.py`):

```python
resolve(document, pointer: str) -> JSONValue
PointerError            # base
PointerSyntaxError      # malformed pointer
KeyNotFound             # dict key missing
IndexOutOfBounds        # list index >= len, negative, or "-"
TypeMismatch            # indexing a non-container
```

## Functions

### Public

- `resolve(document: JSONValue, pointer: str) -> JSONValue`
  - Top-level entry. Calls `_parse(pointer)` then folds `_resolve_token` over the token list with `document` as the initial accumulator.

### Internal (underscore-prefixed, not re-exported)

- `_parse(pointer: str) -> list[str]`
  - Validates syntax; splits on `/`; unescapes each token.
  - Returns `[]` for `""`.
  - Raises `PointerSyntaxError` for: non-empty pointer not starting with `/`, trailing lone `~`, `~` followed by anything other than `0` or `1`.

- `_unescape(token: str) -> str`
  - Applies `~1` → `/` first, then `~0` → `~` (order per RFC §4, flipped order would corrupt `~01`).
  - Assumes validation already happened in `_parse`.

- `_resolve_token(value: JSONValue, token: str) -> JSONValue`
  - If `value` is a `dict`: look up `value[token]` (string key); `KeyNotFound` if missing.
  - If `value` is a `list`: validate `token` is a valid array index (pure `0` or no-leading-zero digits), convert to int, check bounds; `IndexOutOfBounds` for `>= len` or `-`; `PointerSyntaxError` for bad format.
  - Otherwise: `TypeMismatch`.

### Exception classes (in `exceptions.py`)

```python
class PointerError(Exception): ...
class PointerSyntaxError(PointerError, ValueError): ...
class KeyNotFound(PointerError, KeyError): ...
class IndexOutOfBounds(PointerError, IndexError): ...
class TypeMismatch(PointerError, TypeError): ...
```

Multi-inheritance from the stdlib exceptions is deliberate: lets callers use `except ValueError:` or `except KeyError:` naturally while still permitting `except PointerError:` for the library-aware path. Flag this as a decision: the idea did not specify it, and the alternative is "inherit from Exception only." I recommend dual inheritance for ergonomics; worth confirming.

## Test strategy

### Category 1 — RFC §5 vectors (12 cases)

One test function per vector from `rfc6901_vectors.md`. Each is a one-line `assert resolve(doc, PTR) == EXPECTED`. The `""` case uses `is doc` (identity), not `==`.

### Category 2 — Error cases (7+ cases)

One test function per error kind, each using `pytest.raises(ExceptionClass)`:

- `PointerSyntaxError`: pointer `"foo"` (missing leading `/`), trailing `"~"`, `"~x"`, leading-zero index `"/a/01"`, negative `"/a/-1"`, float `"/a/1.0"`, `"+1"`, `" 1"`.
- `KeyNotFound`: `{"a": 1}` with `"/b"`.
- `IndexOutOfBounds`: `"/a/2"` on a 2-element list; `"/a/-"` (the dash).
- `TypeMismatch`: `"/a/x"` on `{"a": 1}`.

### Category 3 — Structural edges

- Empty pointer `""` returns `is doc` (identity preserved).
- `"/"` returns the value at key `""`, not the document.
- `"//"` = two empty-string tokens. If `doc[""]` is a scalar: TypeMismatch. If `doc[""] == {"": X}`: returns X.
- Trailing slash `/foo/` = tokens `["foo", ""]`. If `doc["foo"]` is a list: PointerSyntaxError (empty is not a valid index) — **open question**: should this be PointerSyntaxError or IndexOutOfBounds? I recommend PointerSyntaxError: the syntax of the token is wrong, not the value.
- Unicode in keys: `"/café"` against `{"café": 1}` returns `1`. No encoding games.

### Category 4 — Type boundaries

- `resolve(None, "")` returns `None` (the document is `None`, empty pointer returns the document).
- `resolve(None, "/x")` raises `TypeMismatch` (indexing into None).
- `resolve(True, "/x")` raises `TypeMismatch`.
- `resolve("string", "/0")` raises `TypeMismatch` (RFC does not permit indexing strings, even though Python would).

### Category 5 — Escape order (anti-regression)

The RFC vector `"/m~0n"` → 8 already tests this, but add one that *would silently pass* if escape order were reversed:

```python
# If unescape did ~0 before ~1: "~01" → "~1" → "/". Order matters.
assert resolve({"~1": "reverse-order-marker"}, "/~01") == "reverse-order-marker"
# And the inverse:
assert resolve({"/": "slash-key"}, "/~1") == "slash-key"
```

### What we do NOT test

- URI fragment form (`#/foo/0`) — out of scope.
- Mutation (JSON Patch) — out of scope.
- Streaming / partial documents — out of scope.
- Negative indices per Python convention — rejected, tested in Category 2.
- Non-string dict keys (Python `{1: "a"}`): the pointer is a string, so lookup naturally fails as KeyNotFound. No special handling. Flag as a negative boundary.

## Edge cases worth pinning down in the engspecs

These become explicit postconditions or implementation-note bullets, because two reasonable implementations could differ on them:

1. **Escape order.** `_unescape` must apply `~1` before `~0`. Implementation Notes must state this with RFC §4 cited.
2. **Identity on empty pointer.** `resolve(doc, "")` must return `doc` itself (same object), not a copy or a deep-equal value. Postcondition: uses `is`.
3. **Array index format.** Valid indices are `0` or strings matching `[1-9][0-9]*`. Invalid: leading zeros (`01`), whitespace, signs, floats, underscores, hex. Pin in Preconditions of `_resolve_token`.
4. **Dash `-` on read.** Rejected as `IndexOutOfBounds`, not `PointerSyntaxError` — the syntax is valid per RFC, but it refers to a nonexistent element. Pin in Failure Modes.
5. **Empty token between slashes.** `/foo//bar` = `["foo", "", "bar"]`. This is valid pointer syntax; failure (if any) is a key/type issue, not syntax.
6. **Whitespace.** Whitespace in keys is valid (RFC vector `"/ "` → 7). The pointer string is not stripped. Pin in Preconditions.
7. **What is a "JSON value"?** Accept: `dict`, `list`, `str`, `int`, `float`, `bool`, `None`. Reject (as TypeMismatch during descent): `tuple`, `set`, custom classes. Pin in Preconditions of `resolve`.

## Ambiguities in the idea worth resolving now

| # | Ambiguity | Proposed resolution |
|---|-----------|---------------------|
| 1 | Do exceptions inherit from stdlib (KeyError, IndexError, TypeError, ValueError)? | YES. Dual inheritance — callers can use either the library or the stdlib exception. Flag to confirm. |
| 2 | Is `_parse` / `_unescape` public? | NO. Underscore-prefixed, not in `__all__`. Only `resolve` + exceptions are public. |
| 3 | Does `resolve(doc, "")` return identity or a deep-equal copy? | Identity (`is`). RFC says "the whole JSON document"; most natural reading. |
| 4 | Is the dash `-` ever valid for `resolve`? | NO. Always `IndexOutOfBounds`. The dash is only meaningful for JSON Patch, which is out of scope. |
| 5 | What about a pointer like `/foo/` (trailing slash with a list parent)? | `PointerSyntaxError` — empty string is not a valid array index. **Confirm during Stage 3 re-plan.** |
| 6 | Error chaining: should `KeyNotFound` chain via `raise ... from` when wrapping a `KeyError`? | Implementation detail — leave to the impl engspec. Probably yes. |

Items 1 and 5 are the two the human reviewer should explicitly confirm before Stage 2.

## What Stage 3 (re-plan) should look for

After the test engspec is written, re-scan this plan for:

- Error cases we wrote tests for that are not in the error inventory above.
- Behaviors the tests imply that are not in the "edge cases to pin down" section.
- Functions the tests implicitly need that are not in the Functions section (e.g., did tests require a `_validate_index` helper we didn't plan for?).

Any of these is a legitimate plan update, not methodology noise.

## Language / tooling

- Python 3.10+ (for `JSONValue` type alias with `|`).
- stdlib only.
- pytest for tests.
- `pyproject.toml` with `[build-system]` requires `setuptools` or equivalent.
- No runtime dependencies.

## Ready-to-proceed checklist

- [ ] Human reviewer confirms ambiguities #1 (dual inheritance) and #5 (trailing slash = PointerSyntaxError).
- [ ] `rfc6901_vectors.md` reviewed; no surprise vectors missed.
- [ ] Human reviewer agrees the negative boundaries (URI fragments, mutation, string indexing) match what we want to build.

Once those three are green, Stage 2 (write test engspecs) can proceed.
