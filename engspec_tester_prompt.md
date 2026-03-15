# engspec tester: Adversarial Debate for Spec Validation

Use this document as instructions to run adversarial analysis on `.engspec` files. You will find bugs, spec gaps, and missing edge cases through structured Red/Blue/Judge debate, then update the specs with your findings.

**CRITICAL — Model requirement:** You MUST use `model: "opus"` for ALL agents, sub-agents, and tool calls that spawn agents — including Explore, Plan, general-purpose, and any other agent type. No exceptions. Do not use Sonnet or Haiku for any agent in this workflow. When calling the Agent tool, always pass `model: "opus"`. This applies to every agent invocation for the entire duration of this task.

---

## How to use this

```
Read /path/to/engspec_tester_prompt.md for your instructions.

Here is the engspec package: /path/to/<project-name>-engspec.zip
Here is the source repo at: /path/to/repo

Please run adversarial analysis.
```

Or if you already have the specs alongside the source:

```
Read /path/to/engspec_tester_prompt.md for your instructions.

Here is the repo with .engspec files at: /path/to/repo

Please run adversarial analysis on all .engspec files.
```

---

## Phase 1: Load and Understand

### Step 1: Read project context

If given a zip, extract it. Read `project_context.md`, `call_graph.md`, `test_coverage.md`, and `manifest.json`.

If given a repo with inline `.engspec` files, scan for all `.engspec` files and read the source alongside them.

### Step 2: Build the function map

For every `.engspec` file, build a map of:
- Function name → its spec (from the `.engspec`)
- Function name → its source code (from the corresponding source file)
- Function name → its callers and callees (from Context sections)

### Step 3: Identify analysis targets

Prioritize functions for debate:
1. **Weak test coverage** — functions where the spec's Test Strategy or Context says "not tested" or has gaps
2. **Complex call chains** — functions that call many others or are called by many (high composition risk)
3. **Error handling** — functions with Failure Modes sections (recovered/propagated errors are common spec gap sources)
4. **File-level pseudo-functions** — `<file-level>` sections that set up state used by many functions

Skip trivial functions where the spec is clearly complete (simple getters, identity transforms).

---

## Phase 2: Batch into Subgraphs

Group functions into related subgraphs of **at most 10 functions** each, using the call graph:

1. Start from each root function (entry point with no callers in the project)
2. Walk the call graph to collect its callees up to depth 3
3. If a subgraph exceeds 10, split at natural boundaries (module boundaries, separate concerns)
4. Functions that appear in multiple subgraphs are debated in the subgraph where they are most central

Each subgraph is debated independently. Subgraphs can be processed in parallel.

---

## Phase 3: Debate

For each subgraph, run the debate protocol. You play all three roles in sequence within each round. **This is the core of the analysis.**

### The Three Roles

| Role | Sees Source? | Sees Spec? | Sees Project Context? | Goal |
|------|-------------|-----------|----------------------|------|
| **Red** (Attacker) | Yes | Yes | Yes | Find violations, edge cases, ambiguities |
| **Blue** (Defender) | Yes | Yes | Yes | Argue correctness, propose fixes |
| **Judge** | **NO** | Yes | Yes | Rule on each challenge using spec only |

**CRITICAL: The Judge never sees source code.** This forces the spec to be the source of truth. If the spec is too ambiguous for the Judge to rule, that is automatically a SpecGap.

### Round Protocol

For each round, process every function in the subgraph:

**Step 1: Red Agent**

You receive: the function's spec, its source code, callee specs (for composition checks), project context, and all previous findings.

Produce 0-5 challenges. Each challenge has:
- **Category**: one of:
  - `edge_case` — input that satisfies preconditions but produces wrong/unexpected output
  - `postcondition_violation` — code doesn't guarantee a stated postcondition
  - `spec_ambiguity` — spec is unclear enough that two reasonable implementations would differ
  - `composition_gap` — callee's postconditions don't satisfy caller's preconditions
  - `missing_failure_mode` — error path not documented in spec
  - `concurrency_issue` — thread/async safety not addressed
  - `reimplementation_divergence` — re-implementing from spec alone would produce different behavior
- **Concrete input/scenario**: a specific example, not a vague concern
- **Expected vs actual behavior**: what the spec says should happen vs what the code does (or what's ambiguous)
- **Severity**: `critical` (breaks correctness), `major` (edge case with real impact), `minor` (cosmetic or unlikely)

Do NOT repeat challenges from previous rounds. Review all prior findings before producing new ones.

**Step 2: Blue Agent**

You receive: everything Red received, plus Red's challenges.

For each challenge, respond with:
- **Verdict**: `agree`, `disagree`, or `partial`
- **Reasoning**: reference specific spec sections
- If `agree`: propose a fix (spec update, code fix, or test addition)
- If `disagree`: provide a counterargument with evidence from spec/source
- If `partial`: explain what's right and what's wrong about the challenge

**Step 3: Judge Agent**

You receive: the function's spec, project context, Red's challenges, Blue's responses, and previous round rulings. **You do NOT receive source code.**

For each challenge, rule:
- **Bug** → the code violates the spec. Action: `CodeFix` required.
- **SpecGap** → the spec is incomplete or ambiguous. Action: `SpecUpdate` required. Optionally: `TestAddition`.
- **NoIssue** → the challenge is invalid or already covered. Action: `NoAction`. Optionally: `TestAddition`.

If you cannot rule because the spec is ambiguous, that is a **SpecGap** — the spec must be clear enough for someone with no source access to evaluate correctness.

### Output Format Per Round

For each function debated in the round, produce a findings block:

```markdown
### Round {N}: `{function_name}`

#### Red Challenges
1. **[edge_case/major]** When input is an empty dict, the function returns None but postcondition says "returns a non-empty dict."
   - Input: `{}`
   - Expected: non-empty dict per postcondition
   - Actual: returns None

#### Blue Responses
1. **disagree** — The precondition says "input must be non-empty." Empty dict violates the precondition, so the postcondition doesn't apply.

#### Judge Rulings
1. **NoIssue** — Blue is correct. The precondition excludes empty input. However, the Failure Modes section should document what happens when an empty dict is passed. Action: SpecUpdate (add failure mode).
```

---

## Phase 4: Apply Findings

After each round, apply findings immediately:

### SpecGap Rulings → Update the .engspec file

For each SpecGap ruling:
1. Identify which section needs updating (Preconditions, Postconditions, Failure Modes, Implementation Notes, etc.)
2. Add the missing information directly to the `.engspec` file
3. Add a Debate Log entry to the function's section:

```markdown
### Debate Log
| Round | Agent | Finding | Ruling | Action |
|-------|-------|---------|--------|--------|
| 1 | Red | Empty dict returns None, not documented | SpecGap | Added to Failure Modes |
| 2 | Red | Composition gap: callee doesn't guarantee non-null | SpecGap | Added precondition to caller |
```

### Bug Rulings → Log for review

Do not auto-fix bugs. Log them in the report with:
- Function name and location
- The challenge that found it
- The Judge's reasoning
- Suggested fix (from Blue's proposal)

### NoIssue Rulings with TestAddition

If the Judge suggests adding a test even though there's no issue, note it in the report under "Suggested Tests."

---

## Phase 5: Convergence

Track findings across rounds. The analysis is complete when you reach convergence or hit the hard cap.

### Deduplication

Before counting a round's findings, deduplicate against all previous findings. Two findings are duplicates if they describe the same behavioral concern, even if worded differently:
- "empty list raises ValueError" ≈ "passing [] causes ValueError" → duplicate
- "empty list raises ValueError" vs "None input raises TypeError" → distinct

### Convergence criteria

- **Converged**: 3 consecutive rounds with zero novel findings (after dedup) across all functions in the subgraph
- **Hard cap**: 20 rounds per subgraph — stop even if not converged
- If not converged after 20 rounds, note this in the report

### Confidence score

After convergence (or hard cap), compute a confidence score per subgraph:

```
confidence = 0.3 * round_factor + 0.4 * resolution_rate + 0.3 * clean_factor

round_factor    = min(total_rounds / 10, 1.0)
resolution_rate = resolved_findings / total_findings  (1.0 if no findings)
clean_factor    = consecutive_clean_rounds / 3         (capped at 1.0)
```

---

## Phase 6: Report

After all subgraphs have converged (or hit the cap), produce a report.

### Report format

```markdown
# Adversarial Analysis Report: <project-name>

## Summary
- Functions analyzed: N
- Subgraphs: N
- Total rounds: N
- Findings: N (Bug: N, SpecGap: N, NoIssue: N)
- Spec updates applied: N
- Overall confidence: X.XX

## Findings by Severity

### Critical
- `function_name` [Bug]: description (Round N)

### Major
- `function_name` [SpecGap]: description (Round N) — FIXED in spec

### Minor
- `function_name` [SpecGap]: description (Round N) — FIXED in spec

## Bugs Found (require human review)
| Function | Description | Suggested Fix | Round |
|----------|-------------|---------------|-------|

## Spec Updates Applied
| Function | Section Updated | What was added | Round |
|----------|----------------|----------------|-------|

## Suggested Tests
| Function | Test Description | From Round |
|----------|-----------------|------------|

## Confidence Scores
| Subgraph | Functions | Rounds | Findings | Resolved | Confidence |
|----------|-----------|--------|----------|----------|------------|

## Convergence Details
| Subgraph | Converged? | Clean Rounds | Total Rounds |
|----------|-----------|--------------|--------------|
```

### Output artifacts

1. **Updated `.engspec` files** — with Debate Log entries and spec fixes applied
2. **Report** — `<project-name>-analysis-report.md`
3. **Updated zip** — repackage as `<project-name>-engspec-tested.zip` with the improved specs

---

## Key Principles

1. **The Judge never sees source.** This is the most important constraint. If you're tempted to show the Judge source code to help it rule, don't — an ambiguous spec is a SpecGap, and that's a valid finding.

2. **Concrete over abstract.** Every Red challenge must have a specific input and expected behavior. "This might fail" is not a challenge. "Passing `[]` returns `None` but postcondition says non-empty" is.

3. **Fix specs immediately.** Don't accumulate SpecGap findings for a batch update. Fix them after each round so subsequent rounds debate against the improved spec.

4. **Don't repeat yourself.** Review all prior findings before each Red round. Repeating a finding wastes a round toward the convergence cap.

5. **Composition is where bugs hide.** The most valuable challenges are composition gaps — where function A's postconditions don't satisfy function B's preconditions. These are invisible when looking at functions in isolation.

6. **Severity matters.** A critical finding that breaks correctness is worth more than five minor cosmetic issues. Prioritize accordingly.
