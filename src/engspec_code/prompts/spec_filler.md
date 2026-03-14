# Spec Filler Prompt

You are filling in a skeleton `.engspec` specification from the source code.

## Your Task

Given:
- A skeleton `.engspec` file with placeholder sections
- The corresponding source code file
- The `input_processed.md` context document

Fill in ALL placeholder sections (`<!-- TO BE FILLED BY AGENT -->`) with detailed, precise specifications.

## Section Guidelines

### Preconditions
- List ALL requirements on inputs (types, ranges, valid states)
- Include implicit assumptions (e.g., "tensor must be on same device")
- Be specific: "N >= 1" not just "valid input"

### Postconditions
- What the function guarantees about its return value
- What side effects occur (state changes, file writes, etc.)
- Shape/type guarantees on outputs

### Invariants
- Properties that hold before AND after the function call
- State that is preserved (e.g., "does not modify input tensors")
- Determinism guarantees

### Implementation Notes
- Key algorithmic choices that affect correctness
- Performance-relevant details only when they affect behavior
- Keep shorter than the code itself

### Failure Modes
- What exceptions/errors can be raised and when
- Edge cases that produce unexpected results
- Resource exhaustion scenarios

### Test Strategy
- Property-based tests that verify postconditions
- Edge cases to test
- Integration points to verify

## Output

Return the complete `.engspec` file with all sections filled in. Preserve the metadata and format exactly.
