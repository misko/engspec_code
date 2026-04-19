# Call Graph

## Source files

```
resolve.py::resolve(document, pointer)
  → resolve.py::_parse(pointer)
    → resolve.py::_unescape(token)
  → resolve.py::_resolve_token(value, token)
    → raises KeyNotFound / IndexOutOfBounds / PointerSyntaxError / TypeMismatch

__init__.py::<file-level: public API>
  → imports resolve.py::resolve
  → imports exceptions.py::PointerError, PointerSyntaxError, KeyNotFound, IndexOutOfBounds, TypeMismatch
```

No cycles. Dependency order for regeneration:
1. `exceptions.py` (leaf — no intra-project imports)
2. `resolve.py` (imports from `exceptions.py`)
3. `__init__.py` (imports from both)

## Test files

```
test_resolve.py::<file-level: imports>
  → imports json_pointer.resolve, json_pointer.PointerError, ...

test_resolve.py::test_* (25 functions)
  → each calls json_pointer.resolve(...)
  → each uses rfc_doc fixture from file-level (except the handful that build doc inline)
```

Dependency order for regeneration: all `src/*` first, then `tests/*`.
