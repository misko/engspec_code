# Idea: JSON Pointer (RFC 6901) resolver in Python

I want a small Python library that resolves [RFC 6901](https://www.rfc-editor.org/rfc/rfc6901) JSON Pointers against a Python JSON value (a `dict`, `list`, `str`, `int`, `float`, `bool`, or `None`).

Public API — a single function:

```python
def resolve(document, pointer: str):
    """Return the element referenced by `pointer` within `document`."""
```

Behavior, per RFC 6901:

- Empty pointer `""` → the whole document.
- `/foo` → the value at key `"foo"` if `document` is a dict.
- `/foo/0` → the 0th element at `document["foo"]` if that is a list.
- Reference tokens are separated by `/`; the leading `/` is a separator, not part of a token.
- Escaping: `~1` stands for `/`, `~0` stands for `~`. Order matters: un-escape `~1` before `~0` (per §4).
- Array indices are unsigned decimal integers with no leading zeros (except `0` itself).
- Array index `-` refers to the one-past-end insertion point. For read-only `resolve`, reject it.

Errors (each should be its own exception class, all inheriting a `PointerError`):

- `PointerSyntaxError` — pointer does not begin with `/` and is not empty; bad escape sequence; bad index format (`01`, `3.0`, negative).
- `KeyNotFound` — dict does not contain the referenced key.
- `IndexOutOfBounds` — list index is `>= len(list)` or is `-`.
- `TypeMismatch` — trying to index a non-container (number, string, null, bool) with a token.

Scope boundaries — what we are NOT building:

- We are **not** implementing the URI fragment form (`#/foo/0` style); only the string representation of §3.
- We are **not** implementing JSON Patch (RFC 6902) — the `-` index is rejected, not extended.
- We are **not** supporting mutation — this is a read-only resolve.
- No network I/O, no file parsing. Input is an already-parsed Python value.

Language: Python 3.10+, stdlib only. Layout: one package, a handful of functions, pytest.

Please take this idea and produce a plan: what modules/functions we need, what the test strategy should look like, what edge cases to cover, and what's explicitly out of scope.
