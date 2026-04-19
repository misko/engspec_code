# Test Coverage

25 test functions in `test_resolve.py.engspec`. All exercise `resolve` directly; internal functions are covered indirectly.

## `resolve`
- **RFC §5 vectors (12)**: `test_empty_pointer_returns_document`, `test_foo_returns_list`, `test_foo_0_returns_bar`, `test_slash_returns_value_at_empty_key`, `test_escape_tilde_one_to_slash`, `test_percent_in_key`, `test_caret_in_key`, `test_pipe_in_key`, `test_backslash_in_key`, `test_doublequote_in_key`, `test_space_key`, `test_escape_tilde_zero_to_tilde`.
- **Escape order anti-regression (2)**: `test_escape_order_tilde_one_first`, `test_escape_order_slash_key`.
- **Syntax errors (5)**: `test_syntax_error_no_leading_slash`, `test_syntax_error_trailing_tilde`, `test_syntax_error_bad_escape`, `test_syntax_error_leading_zero_index`, `test_syntax_error_negative_index`.
- **Semantic errors (4)**: `test_key_not_found`, `test_index_out_of_bounds`, `test_dash_index_rejected`, `test_type_mismatch_scalar`.
- **Type boundary (1)**: `test_resolve_none_with_empty_pointer`.
- **Base class (1)**: `test_pointer_error_is_base_class`.

## `_parse`
- Indirect via `resolve`. Syntax errors are the direct coverage: leading-slash check, trailing-tilde check, bad-escape check.
- **Not directly tested**: empty pointer returning `[]`. Covered indirectly via `test_empty_pointer_returns_document` (identity short-circuits before `_parse` is called — this is a coverage gap for `_parse` specifically, but `resolve` is correct regardless).

## `_unescape`
- Indirect via `resolve`. Direct tests: `test_escape_tilde_one_to_slash`, `test_escape_tilde_zero_to_tilde`, `test_escape_order_tilde_one_first`, `test_escape_order_slash_key`.

## `_resolve_token`
- Indirect via `resolve`. Every non-empty-pointer test exercises it. Every Failure Mode is exercised by at least one test.

## Coverage gaps (known, accepted)

- `_parse("")` returning `[]` is not directly tested — `resolve` short-circuits first. Not a correctness gap since the behavior is observable only through `resolve`, which is tested.
- Structural edges (`//`, `/foo/`) from plan.md §3 are not tested in this v1 — deliberate deferral; the escape-order tests cover the subtlest case.
- Very large documents, very deep nesting — no performance tests; not part of the contract.
