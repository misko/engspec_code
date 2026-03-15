# engspec tester: Adversarial Debate for Spec Validation

Use this document as instructions to run adversarial analysis on `.engspec` files. You will find spec gaps, ambiguities, internal contradictions, and missing edge cases through structured Red/Blue/Judge debate, then update the specs with your findings.

**Two modes of operation:**
- **Spec + Source** (recommended): provide both the engspec package and the source repo. Red and Blue see source code, enabling them to find divergence between spec and implementation. The Judge still never sees source.
- **Spec only**: provide just the engspec package. All roles work from specs alone. Use this when source code is unavailable.

**CRITICAL — Model requirement:** You MUST use `model: "opus"` for ALL agents, sub-agents, and tool calls that spawn agents — including Explore, Plan, general-purpose, and any other agent type. No exceptions. Do not use Sonnet or Haiku for any agent in this workflow. When calling the Agent tool, always pass `model: "opus"`. This applies to every agent invocation for the entire duration of this task.

---

## How to use this

### Spec + Source (recommended)

```
Read /path/to/engspec_tester_prompt.md for your instructions.

Here is the engspec package at: /path/to/<project-name>-engspec/
Here is the source repo at: /path/to/repo

Please run adversarial analysis.
```

### Spec only

```
Read /path/to/engspec_tester_prompt.md for your instructions.

Here is the engspec package at: /path/to/<project-name>-engspec/

Please run adversarial analysis.
```

---

## Phase 1: Load and Understand

### Step 1: Read project context

If given a zip, extract it. You should find:

```
<project-name>-engspec/
├── project_context.md
├── call_graph.md
├── test_coverage.md
├── manifest.json
├── specs/
│   └── ... .engspec files
└── non_code/
    └── ... config, docs, assets
```

Read `project_context.md`, `call_graph.md`, `test_coverage.md`, and `manifest.json`.

If source repo is provided, verify that the `.engspec` files correspond to the source files.

### Step 2: Build the function map

For every `.engspec` file, build a map of:
- Function name → its full spec (Purpose, Preconditions, Postconditions, etc.)
- Function name → its source code (if source repo is provided)
- Function name → its callers and callees (from Context sections)
- Function name → which spec file it lives in

### Step 3: Identify analysis targets

Prioritize functions for debate:
1. **Weak test coverage** — functions where the Context or Test Strategy says "not tested" or has gaps
2. **Complex call chains** — functions that call many others or are called by many (high composition risk)
3. **Error handling** — functions with Failure Modes sections (recovered/propagated errors are common gap sources)
4. **File-level pseudo-functions** — `<file-level>` sections that set up state used by many functions
5. **Negative boundaries** — functions whose Purpose mentions what they do NOT implement (these are easy to under-specify)

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
| **Red** (Attacker) | Yes (if available) | Yes | Yes | Find violations, ambiguities, gaps, composition failures |
| **Blue** (Defender) | Yes (if available) | Yes | Yes | Argue correctness, propose fixes |
| **Judge** (Arbiter) | **NEVER** | Yes | Yes | Rule on each challenge using spec only |

**CRITICAL: The Judge never sees source code, even when source is available.** This forces the spec to be the source of truth. If the spec is too ambiguous for the Judge to rule, that is automatically a SpecGap — regardless of whether the source code handles it correctly.

### Red Agent Attack Strategies

**When source is available**, Red compares spec against implementation:

1. **Spec-source divergence**: Does the source do something the spec doesn't describe? Does the spec describe something the source doesn't do?
2. **Undocumented behavior**: Does the source handle edge cases not mentioned in the spec?
3. **Wrong negative boundaries**: Does the source implement behaviors the Purpose says it excludes?
4. **Missing error paths**: Does the source catch/handle errors not listed in Failure Modes?
5. **Third-party API details**: Does the source call third-party APIs with kwargs or arguments not captured in Implementation Notes?

**Whether or not source is available**, Red also attacks the spec itself:

6. **Reimplementation test**: Re-implement the function from the spec alone. If the spec is ambiguous enough that two reasonable implementations would differ, that's a challenge.
7. **Precondition/Postcondition consistency**: Could a valid input (satisfying all preconditions) produce output that violates a postcondition?
8. **Composition verification**: Walk the call graph. Does each callee's postconditions satisfy the caller's preconditions?
9. **Failure mode completeness**: For each precondition, what happens when it's violated? Is there a corresponding failure mode?
10. **Cross-function state**: Do functions that share mutable state have consistent invariants?
11. **Test strategy gaps**: Does the Test Strategy cover all postconditions, failure modes, and edge cases?

### Round Protocol

For each round, process every function in the subgraph:

**Step 1: Red Agent**

You receive: the function's spec, callee specs (for composition checks), project context, call graph, all previous findings, and source code (if available).

Produce 0-5 challenges. Each challenge has:
- **Category**: one of:
  - `spec_source_divergence` — source does something spec doesn't capture (only when source available)
  - `spec_ambiguity` — two reasonable implementations from this spec would differ
  - `composition_gap` — callee's postconditions don't satisfy caller's preconditions
  - `missing_failure_mode` — precondition violation behavior not documented
  - `postcondition_gap` — postcondition doesn't cover an output case
  - `negative_boundary_leak` — excluded behavior not sufficiently constrained
  - `invariant_conflict` — shared state invariants between functions are inconsistent
  - `test_coverage_gap` — postcondition or failure mode with no test strategy
- **Concrete scenario**: a specific input or call sequence, not a vague concern
- **The gap**: what's missing, ambiguous, or contradictory — and how it would cause incorrect regeneration
- **Severity**: `critical` (would cause incorrect regeneration), `major` (edge case with real impact), `minor` (unlikely or cosmetic)

Do NOT repeat challenges from previous rounds. Review all prior findings before producing new ones.

**Step 2: Blue Agent**

You receive: everything Red received, plus Red's challenges.

For each challenge, respond with:
- **Verdict**: `agree`, `disagree`, or `partial`
- **Reasoning**: reference specific spec sections
- If `agree`: propose a spec fix (which section, what to add/change)
- If `disagree`: explain why the spec already covers this, citing specific bullets
- If `partial`: explain what's covered and what's missing

**Step 3: Judge Agent**

You receive: the function's spec, project context, Red's challenges, and Blue's responses. **You do NOT receive source code, even when it was available to Red and Blue.**

For each challenge, rule:
- **SpecGap** → the spec is incomplete or ambiguous. Action: `SpecUpdate` required. Specify which section and what to add.
- **NoIssue** → the spec already covers this adequately. Blue's defense holds. Action: `NoAction`.
- **SpecConflict** → two parts of the spec contradict each other. Action: `SpecUpdate` to resolve the contradiction.

Optionally for any ruling: recommend a `TestAddition` to the Test Strategy section.

### Output Format Per Round

For each function debated in the round, produce a findings block:

```markdown
### Round {N}: `{function_name}`

#### Red Challenges
1. **[spec_ambiguity/major]** Postcondition says "returns normalized URL" but Implementation Notes don't define normalization. A regenerator could implement WHATWG normalization (lowercase scheme + host, resolve dots) or minimal RFC 3986 (percent-encoding only). These produce different outputs for `HTTP://Example.COM/../foo`.
   - Scenario: input `HTTP://Example.COM/../foo`
   - Implementation A (WHATWG): `http://example.com/foo`
   - Implementation B (RFC 3986 minimal): `HTTP://Example.COM/../foo`

#### Blue Responses
1. **partial** — Purpose says "follows RFC 3986 only, does NOT implement WHATWG." This constrains the normalization. However, RFC 3986 itself has multiple normalization levels (case, percent-encoding, path-segment). The spec should specify which level.

#### Judge Rulings
1. **SpecGap** — Purpose excludes WHATWG but doesn't specify the RFC 3986 normalization level. Action: SpecUpdate — add to Implementation Notes: "Applies RFC 3986 Section 6.2.2 syntax-based normalization (case, percent-encoding, path-segment removal)."
```

---

## Phase 4: Apply Findings

After each round, apply findings immediately:

### SpecGap / SpecConflict Rulings → Update the .engspec file

For each SpecGap or SpecConflict ruling:
1. Identify which section needs updating (Preconditions, Postconditions, Failure Modes, Implementation Notes, Purpose, etc.)
2. Add the missing information directly to the `.engspec` file
3. Add a Debate Log entry to the function's section:

```markdown
### Debate Log
| Round | Agent | Finding | Ruling | Action |
|-------|-------|---------|--------|--------|
| 1 | Red | Normalization level not specified | SpecGap | Added RFC 3986 §6.2.2 to Implementation Notes |
| 2 | Red | Composition gap: callee doesn't guarantee non-null | SpecGap | Added precondition to caller |
```

### NoIssue Rulings with TestAddition

If the Judge suggests adding a test even though the spec is adequate, add it to the Test Strategy section of the `.engspec` file.

---

## Phase 5: Convergence

Track findings across rounds. The analysis is complete when you reach convergence or hit the hard cap.

### Deduplication

Before counting a round's findings, deduplicate against all previous findings. Two findings are duplicates if they describe the same spec concern, even if worded differently:
- "empty list behavior not specified" ≈ "passing [] has undefined result" → duplicate
- "empty list behavior not specified" vs "None input not in failure modes" → distinct

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
- Mode: spec + source / spec only
- Functions analyzed: N
- Subgraphs: N
- Total rounds: N
- Findings: N (SpecGap: N, SpecConflict: N, NoIssue: N)
- Spec updates applied: N
- Tests added to spec: N
- Overall confidence: X.XX

## Findings by Severity

### Critical
- `function_name` [SpecGap]: description (Round N) — FIXED in spec

### Major
- `function_name` [SpecGap]: description (Round N) — FIXED in spec

### Minor
- `function_name` [SpecGap]: description (Round N) — FIXED in spec

## Spec Conflicts Found
| Function | Contradiction | Resolution | Round |
|----------|--------------|------------|-------|

## Spec Updates Applied
| Function | Section Updated | What was added | Round |
|----------|----------------|----------------|-------|

## Tests Added to Spec
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
3. **Updated package** — repackage as `<project-name>-engspec-tested.zip` (or update in place if working from an extracted directory)

---

## Key Principles

1. **The Judge never sees source.** Even when Red and Blue have source access, the Judge evaluates purely against the spec. If the spec is ambiguous enough that the Judge can't rule, that's a SpecGap — even if the source code handles it correctly. The spec must stand on its own.

2. **Concrete over abstract.** Every Red challenge must have a specific scenario. "This might be ambiguous" is not a challenge. "Input `HTTP://Example.COM/../foo` would produce different output under WHATWG vs RFC 3986 normalization" is.

3. **Fix specs immediately.** Don't accumulate SpecGap findings for a batch update. Fix them after each round so subsequent rounds debate against the improved spec.

4. **Don't repeat yourself.** Review all prior findings before each Red round. Repeating a finding wastes a round toward the convergence cap.

5. **Composition is where gaps hide.** The most valuable challenges are composition gaps — where function A's postconditions don't satisfy function B's preconditions. These are invisible when looking at functions in isolation.

6. **Reimplementation is the primary attack.** Red's strongest tool is reimplementing a function from spec alone and showing where two reasonable implementations would diverge. If the spec allows divergence, it's a SpecGap.

7. **Source access amplifies Red.** When source is available, Red can compare spec against actual implementation to find undocumented behavior, missing error paths, and third-party API details not captured in the spec. These are the findings that most improve spec quality.

8. **Severity matters.** A critical finding that would cause incorrect regeneration is worth more than five minor cosmetic issues. Prioritize accordingly.
