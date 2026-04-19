# Project Context (auto-generated)

**Project**: json_pointer
**Language(s)**: Python 3.10+
**Description**: Read-only resolver for RFC 6901 JSON Pointers against in-memory Python JSON values (dict/list/str/int/float/bool/None). Public API is a single function `resolve(document, pointer)` plus five exception classes. Stdlib-only, no runtime dependencies.

**Structure**:
- `src/json_pointer/__init__.py` — public API re-exports
- `src/json_pointer/resolve.py` — `_parse`, `_unescape`, `_resolve_token`, `resolve`
- `src/json_pointer/exceptions.py` — `PointerError` + 4 subclasses
- `tests/test_resolve.py` — RFC §5 vectors + error paths + anti-regression

**Test setup**:
```bash
pip install -e ".[dev]"
pytest -v
```

**Entry point(s)**: library only, no CLI.

**Notes**:
- Escape order: `~1` → `/` must be applied before `~0` → `~` per RFC 6901 §4. Test `test_escape_order_tilde_one_first` is the anti-regression.
- The dash token `-` refers to the one-past-end insertion point per RFC §4. For read-only resolve, it always raises `IndexOutOfBounds`.
- Empty pointer `""` returns the document by identity (`is`), not a copy.
- Exception classes inherit dually: e.g., `KeyNotFound(PointerError, KeyError)` so both `except PointerError` and `except KeyError` work.
- URI fragment form (`#/foo/0`) is **not** implemented — explicit negative boundary.
- JSON Patch (`-` index as insertion marker, mutation) is **not** implemented.
