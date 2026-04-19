# engspec repo conventions

*Conventions for projects that use the engspec methodology. Read alongside `README.md`'s "Building from scratch" section, which describes the pipeline for producing a single feature.*

## Two modes of using engspec

A codebase relates to its engspec package in one of two ways.

### 1. engspec-retrofitted

The codebase exists; `.engspec` files are written after the fact to document it. Specs trail the code. The relationship is descriptive: if code and spec disagree, the code is the source of truth and the spec needs to be re-derived.

This is what `engspec_prompt.md` produces when you point it at an existing repo: a spec package that mirrors what's there. Useful for auditing an unfamiliar codebase, handing off ownership, or preparing for adversarial debate.

### 2. engspec-first

The engspec package is authored **before** any code. Specs lead the code. Code is derived from specs via `engspec_to_code_prompt.md`. The relationship is prescriptive: if code and spec disagree, the **spec is the source of truth** and the code gets re-derived.

This is the stronger commitment and it's the one the full pipeline in the README is designed around:

```
idea.md → plan.md → test engspecs → plan.v2 → impl engspecs → trace → regen → pytest
```

In an engspec-first repo:

- **No code change lands without a spec change first.** If a runtime bug surfaces a spec gap, the bug fix is: update the relevant engspec, re-trace the affected test, re-generate the code. The code change is the *last* step, not the first.
- **Drift between spec and code is itself a bug.** A commit that updates code without updating specs is incomplete. Treat it the same way you'd treat a commit that updated production code but didn't update the tests.
- **Spec debt is visible.** Every impl engspec has a `<!-- plan_vN_applied: true|false -->` or similar marker for the most recent plan revision. A stale marker means the file is behind; a current marker means spec and code are in sync.

## When to choose each mode

Pick **engspec-retrofitted** when:
- You have existing code you didn't write and need to understand quickly.
- You're preparing for an adversarial debate on someone else's codebase.
- You want AI-assisted documentation without enforcing spec-first discipline.

Pick **engspec-first** when:
- You're starting a new project and want the methodology to guide development.
- Correctness matters more than velocity.
- Multiple contributors (including AI agents) need a shared source of truth that isn't the code.
- You want the trace mechanism to catch cross-cutting design issues before any code exists (see the `watch.engspec` trace example in the tests/json_pointer case study for what this looks like in practice).

## Enforcement mechanisms for engspec-first repos

Four practices keep drift low:

### 1. Declare the mode at the top of the repo's README

```markdown
**Status:** engspec-first. The canonical source of truth is `package/specs/`.
Code under `src/` is regenerated from specs; never edit code without first
updating the corresponding spec.
```

### 2. Use plan.vN markers

When you learn something from runtime that changes the spec, write a new `plan.vN.md` documenting the delta. Then update the affected engspecs with `<!-- plan_vN_applied: true -->`. CI can grep for stale markers.

### 3. Trace new cross-cutting features before writing code

For any feature that touches many existing specs (e.g., inotify event emission needing mutation-method changes across fs.py), write a trace for one representative test case first. If the trace concludes UNCLEAR, the design isn't ready — fix the specs, re-trace, iterate. Only start coding once the trace PASSes.

This is the step that most distinguishes engspec-first from engspec-retrofitted: in the first mode, UNCLEAR traces surface design problems *before* they hit code. In the second mode, the same problems surface as bugs.

### 4. Debt is named

When a code change has landed without its spec update (rare in the disciplined case, but happens in practice under time pressure), record it explicitly in a `methodology_findings.md` or equivalent. The debt is visible; the fix is scheduled.

## Example: sqlite-fs

[sqlite-fs](https://github.com/...) is an engspec-first repo built using this methodology. It tracks spec-vs-code alignment via `plan.v1.md`, `plan.v2.md`, `plan.v3.md` files that record every deviation between what the specs said and what runtime taught. Impl engspecs carry `<!-- plan_v3_applied: true -->` markers. Watch-directory support (a v2 feature) was designed entirely in spec form first, and the first trace for a planned test concluded UNCLEAR — surfacing a cross-cutting design gap (events need to be emitted from every mutating method) before any code was written.

## Operational implications for AI agents

Agents working on an engspec-first repo must:

1. Read `package/specs/` before `src/`. The specs are authoritative.
2. Never propose a code-only change. Every code diff must be accompanied by the corresponding spec diff.
3. When a runtime test surfaces a bug, the fix workflow is: document the finding → update the engspec → trace the affected test → regenerate (or edit) the code → re-run tests. In that order.
4. Flag drift. If the agent sees code that doesn't match its spec, that's a finding, not "fine because it works."
