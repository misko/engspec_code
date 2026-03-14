# engspec: Code → English Specification (Single-File Prompt)

Use this document as instructions to produce a validated `.engspec` specification for any source file. Works with any language.

**CRITICAL — Model requirement:** You MUST use `model: "opus"` for ALL agents, sub-agents, and tool calls that spawn agents — including Explore, Plan, general-purpose, and any other agent type. No exceptions. Do not use Sonnet or Haiku for any agent in this workflow. When calling the Agent tool, always pass `model: "opus"`. This applies to every agent invocation for the entire duration of this task.

---

## How to use this

### Option A: You have source files ready

```
Here is my prompt: engspec_prompt.md
Here is my source file: <paste or attach file>
Here is project context: <brief description of what the project does, how to run tests, etc.>

Please produce a validated .engspec for this file.
```

### Option B: You have a local repo

```
Here is my prompt: engspec_prompt.md
Here is my repo at /path/to/repo
Please produce .engspec files for all source files.
```

### Option C: You only have a git URL (no input.md, no local files)

```
Here is my prompt: engspec_prompt.md

Please clone <git-url>, analyze the repo, and produce .engspec files for all source files.
```

When no `input.md` or project context is provided, **you must auto-generate it**.
See Phase 1 below.

---

## Phase 1: Project Context

Before analyzing code, establish context. Use whichever source is available, in priority order:

### If the user provided an `input.md`:
Read it and proceed to Phase 2.

### If the user provided a local repo path or git URL (no `input.md`):
Auto-generate context by examining the repo. Read these files (whichever exist):

1. **README.md**, **CONTRIBUTING.md**, **CHANGELOG.md** — project description, conventions
2. **Build files** — `pyproject.toml`, `Cargo.toml`, `package.json`, `go.mod`, `CMakeLists.txt`, `Makefile`, `justfile`
3. **CI configs** — `.github/workflows/*.yml`, `.gitlab-ci.yml`, `.circleci/config.yml`
4. **Test directories** — `tests/`, `test/`, `spec/`, `__tests__/` — scan for test patterns, frameworks, commands
5. **Source structure** — `ls` the tree to understand layout
6. **Git history** — `git log --oneline -20` for recent activity context
7. **Docstrings / comments** — skim main entry points for inline docs

From this, produce a **Project Context** summary (this is your auto-generated `input.md`):

```markdown
## Project Context (auto-generated)

**Project**: <name>
**Language(s)**: <detected languages>
**Description**: <what it does, key abstractions>
**Structure**: <key directories and what they contain>
**Test setup**: <how to install deps and run tests, or "no tests found">
**Entry point(s)**: <main files, CLI commands, etc.>
**Notes**: <anything else relevant — conventions, external deps, known quirks>
```

Share this summary with the user before proceeding, so they can correct anything.

### If the user provided individual files (no repo):
Infer what you can from the code itself. Note gaps ("no test information available — skipping test coverage analysis").

---

## Phase 2: Deep Analysis

For the source file(s), analyze and produce (share with the user):

### Call Graph
Trace the major call paths as trees:
```
function_a()
  → function_b()
    → function_c()
  → function_d()
```

### Test Coverage
For each function, note:
- What tests exist (file, what they check)
- What is NOT tested (gaps)

---

## Phase 3: Generate .engspec

Produce one `.engspec` file per source file. **Copy the template below exactly. Fill in the placeholders. Do not invent your own format, reorder sections, rename headings, or add custom structure.**

### THE TEMPLATE

Every `.engspec` file MUST follow this structure. Copy it, fill in the `{placeholders}`, remove sections that don't apply, but never rename or reorder anything.

````markdown
<!-- engspec v1 -->
<!-- source: {relative/path/to/source.ext} -->
<!-- language: {python|rust|go|cpp|c|javascript|typescript|java} -->
<!-- hash: sha256:{actual hash of source file} -->
<!-- status: {skeleton|validated|failed} -->
<!-- validated: {ISO 8601 timestamp, omit if not yet validated} -->
<!-- regeneration_count: {total attempts, omit if not yet validated} -->
<!-- regeneration_pass_rate: {5/5 for validated, omit if not yet validated} -->

## `{function_name(param1: Type, param2: Type) -> ReturnType}`

### Purpose
{1-3 sentences. What and why, not how.}

### Context
- Called by: {caller1(), caller2()}
- Calls: {callee1(), callee2()}
- Test coverage: {what's tested, what's not}

### Preconditions
{- Each precondition on its own bullet}
{- Be specific: "n >= 1" not "valid input"}
{- Include constants this function depends on: "TICK_RATE controls frame cap, currently 60"}

### Postconditions
{- Each guarantee on its own bullet}
{- Include return value, side effects, and what is NOT modified}

### Invariants
{- Properties preserved before and after the call}

### Implementation Notes
{- Only what affects correctness. MUST be shorter than the source code.}

### Failure Modes
{- Concrete: "Raises ValueError if n < 0", not "may raise errors"}
{- For each error, state: **recovered** (caught, fallback, continues) or **propagated** (re-raised to caller)}
{- Example: "If X fails: **recovered** — sets fallback_value, continues"}
{- Example: "If Y fails: **propagated** — closes handle, re-raises to caller"}

### Test Strategy
{- Actionable bullets. Someone should be able to write tests from this alone.}

---
````

**Note:** A `### Debate Log` section may appear in `.engspec` files after adversarial review by `engspec_tester`. Do NOT add it during `code→engspec` generation — it is added later by the tester's Red/Blue/Judge debate cycle.

### Rules for using the template

**Every section uses exactly these heading names, in this order.** If a section doesn't apply to a particular function (e.g., a pure function has no Failure Modes), omit the section entirely — don't include it with "N/A" or empty content.

**The `##` heading MUST be the function signature in backticks.** For regular functions:
```
## `function_name(param1: Type, param2: Type) -> ReturnType`
```

**For file-level code** (top-level execution, mutable globals, interrelated constants), use the same template with a pseudo-function signature:
```
## `<file-level: description>`
```

A file can have multiple `<file-level>` sections:
- `## \`<file-level: initialization>\`` — imports, setup calls, global init
- `## \`<file-level: state>\`` — mutable globals, interrelated constants
- `## \`<file-level: main loop>\`` — entry point / main block

**When to use `<file-level>`:**

| Situation | Action |
|-----------|--------|
| File has top-level execution (runs on import/load/execute) | Add a `<file-level>` section |
| File has mutable globals or interrelated constants | Add a `<file-level: state>` section |
| File has only simple constants (`PI = 3.14`) | No section — mention in function Preconditions |
| File has nothing but functions | No section |

For languages where everything is a function (Rust, Go, Java), `<file-level>` is rarely needed. `fn main()` and `func init()` are real functions and get regular sections.

**What to skip entirely:**
- Trivial getters/setters (unless they have validation logic)
- `__repr__`, `__str__` (unless complex formatting)
- Auto-generated code (unless the generation has important constraints)

If a function's behavior is fully captured by its signature, Purpose alone is enough — omit other sections.

### Section guidance

| Section | Key rule |
|---------|----------|
| Purpose | 1-3 sentences. What and why, not how. |
| Context | Callers, callees, test coverage status. |
| Preconditions | Every input constraint. If a function silently accepts invalid input, note what happens. |
| Postconditions | Every output guarantee. Include mutation guarantees ("input list is not modified"). |
| Invariants | What doesn't change. Important for stateful objects. |
| Implementation Notes | Only what affects correctness. Algorithm choice, not code style. SHORTER than source. |
| Failure Modes | Concrete exceptions and conditions. Not "may raise errors". For each error, specify whether it is **recovered** (caught, fallback applied, execution continues) or **propagated** (re-raised to caller). Example: "If lstat raises FileNotFoundError: **recovered** — sets original_mode to None and continues without mode preservation." vs "If lstat raises PermissionError: **propagated** — closes file handle, then re-raises to caller." |
| Test Strategy | Actionable. Someone writes tests from this section alone. |

---

## Phase 4: Regeneration Verification

This is the critical validation step. The spec is not done until **5 consecutive regenerations all pass without any spec changes between them**.

### Overview

```
regeneration_number = 0
consecutive_passes = 0

while consecutive_passes < 5:
    regeneration_number += 1
    if regeneration_number > 20:
        ERROR: spec failed to converge after 20 regenerations

    result = regenerate_and_compare()

    if result == PASS:
        consecutive_passes += 1
    else:
        fix the spec based on what was missing
        consecutive_passes = 0    # reset — need 5 clean in a row
```

**Hard limit: 20 total regenerations.** If you cannot achieve 5 consecutive passes within 20 regenerations, mark the spec as `status: failed` and report what could not be captured.

### Per-regeneration procedure

**Step 1: Re-implement from spec alone**

Pretend you cannot see the original source code. Using ONLY the `.engspec` you wrote, re-implement the function from scratch. Rules:
- You have NO access to the original source
- The reimplementation does NOT need to be character-identical
- It MUST satisfy all preconditions, postconditions, invariants, and failure modes
- Choose the most natural implementation given only the spec
- Each regeneration must be independent — do NOT copy from previous attempts

**Step 2: Compare against original**

| Check | Question |
|-------|----------|
| Preconditions | Does the reimplementation assume/check the same input constraints? |
| Postconditions | Does it guarantee the same outputs and effects? |
| Failure modes | Does it handle the same error cases? |
| Algorithmic properties | Are the core algorithmic behaviors preserved? |
| Side effects | Are side effects identical? |

Things that DON'T matter: code style, variable names, comments, import order, performance (unless specified in Implementation Notes).

**Step 3: Rule PASS or FAIL**

- **PASS**: The reimplementation preserves all essential properties. Increment `consecutive_passes`.
- **FAIL**: The reimplementation missed something because the spec was incomplete. Identify exactly what the spec failed to communicate. Update the spec. Reset `consecutive_passes` to 0.

### Convergence

The spec is **validated** when you achieve 5 consecutive PASS results with no spec edits in between. This proves the spec is sufficient for any independent reader to reproduce the behavior.

### Update metadata

After convergence (5/5 consecutive passes):
```markdown
<!-- status: validated -->
<!-- validated: <timestamp> -->
<!-- regeneration_count: <total attempts, e.g. 8> -->
<!-- regeneration_pass_rate: 5/5 -->
```

`regeneration_count` is the TOTAL number of regenerations performed (including failures). `regeneration_pass_rate` is always `5/5` for a validated spec — it means the final 5 consecutive attempts all passed.

If the spec fails to converge after 20 regenerations:
```markdown
<!-- status: failed -->
<!-- regeneration_count: 20 -->
<!-- regeneration_pass_rate: <best consecutive run, e.g. 3/5> -->
<!-- failure_reason: <what could not be captured> -->
```

### Example trace

```
Regeneration  1: FAIL — spec didn't mention clamping behavior → fix spec, reset to 0
Regeneration  2: FAIL — spec didn't specify collision order → fix spec, reset to 0
Regeneration  3: PASS — consecutive: 1
Regeneration  4: PASS — consecutive: 2
Regeneration  5: PASS — consecutive: 3
Regeneration  6: PASS — consecutive: 4
Regeneration  7: PASS — consecutive: 5 → VALIDATED (7 total, 5/5 final)
```

---

## Phase 5: Self-Review (Optional but Recommended)

After completing the `.engspec`, do a final adversarial pass:

### Red Team (find problems)
For each function, ask:
- Is there an input that satisfies all preconditions but produces wrong output?
- Is there a postcondition that the implementation doesn't actually guarantee?
- Is there a failure mode not listed?
- Could a caller reasonably violate a precondition that isn't documented?

### Blue Team (defend or fix)
For each finding:
- Is it a real issue or a misreading of the spec?
- If real: update the spec with the missing information
- If not: explain why the spec is correct as-is

### Record findings
If you find real issues during self-review, fix them directly in the spec (update the relevant section). No need to log them — the formal Debate Log is added later by `engspec_tester`.

---

## Output Checklist

Before delivering the `.engspec` file, verify:

- [ ] Every public function/method has a section
- [ ] File-level pseudo-functions exist for top-level execution, mutable globals, or interrelated constants (if applicable)
- [ ] All metadata comments are present and accurate
- [ ] Preconditions are specific (no vague "valid input")
- [ ] Postconditions cover return values AND side effects
- [ ] Failure modes list concrete exceptions/conditions
- [ ] Test strategy is actionable (someone could write tests from it)
- [ ] Implementation Notes are SHORTER than the source code
- [ ] Regeneration verification passed: 5 consecutive passes within 20 total attempts
- [ ] Status is `validated` with `regeneration_pass_rate: 5/5`
- [ ] The spec reads as self-contained English — no "see code for details"

---

## Example: Function-only file

For a simple function like:
```python
def fibonacci(n: int) -> int:
    if n < 0:
        raise ValueError("n must be non-negative")
    if n <= 1:
        return n
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b
```

The `.engspec` would be:

```markdown
<!-- engspec v1 -->
<!-- source: math_utils.py -->
<!-- language: python -->
<!-- hash: sha256:a1b2c3... -->
<!-- status: validated -->
<!-- validated: 2026-03-14T12:00:00Z -->
<!-- regeneration_count: 5 -->
<!-- regeneration_pass_rate: 5/5 -->

## `fibonacci(n: int) -> int`

### Purpose
Computes the n-th Fibonacci number (0-indexed: fib(0)=0, fib(1)=1, fib(2)=1, ...).

### Context
- Called by: (varies by project)
- Calls: none
- Test coverage: (fill based on actual tests)

### Preconditions
- n is an integer >= 0

### Postconditions
- Returns the n-th Fibonacci number
- Return value >= 0
- fib(0) = 0, fib(1) = 1, fib(n) = fib(n-1) + fib(n-2) for n >= 2

### Invariants
- Pure function, no side effects
- Deterministic

### Implementation Notes
- Iterative (not recursive), O(n) time, O(1) space

### Failure Modes
- Raises ValueError if n < 0
- For very large n (e.g., n > 10^6), result may be slow due to big integer arithmetic

### Test Strategy
- Property: fib(n) = fib(n-1) + fib(n-2) for n in [2, 20]
- Edge: fib(0) = 0, fib(1) = 1
- Edge: n = -1 raises ValueError
- Large: fib(100) = 354224848179261915075

---
```

No `<file-level>` section needed — the file is just a pure function with no top-level execution, mutable globals, or interrelated constants.

## Example: File with top-level code and state

For a game script like:
```python
import pygame

SCREEN_W, SCREEN_H = 800, 600
TICK_RATE = 60

pygame.init()
screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
clock = pygame.time.Clock()

score = 0
ball_x, ball_y = SCREEN_W // 2, SCREEN_H // 2

def reset_ball():
    global ball_x, ball_y
    ball_x, ball_y = SCREEN_W // 2, SCREEN_H // 2

if __name__ == "__main__":
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        reset_ball()
        clock.tick(TICK_RATE)
    pygame.quit()
```

The `.engspec` would be:

```markdown
<!-- engspec v1 -->
<!-- source: game.py -->
<!-- language: python -->
<!-- hash: sha256:d4e5f6... -->
<!-- status: validated -->
<!-- validated: 2026-03-14T14:00:00Z -->
<!-- regeneration_count: 7 -->
<!-- regeneration_pass_rate: 5/5 -->

## `<file-level: initialization>`

### Purpose
Initializes pygame subsystems and creates the display surface and clock.

### Preconditions
- pygame package is installed
- Display server is available

### Postconditions
- pygame is initialized
- `screen` is a pygame Surface of size (800, 600)
- `clock` is a pygame.time.Clock instance
- SCREEN_W = 800, SCREEN_H = 600, TICK_RATE = 60

### Failure Modes
- pygame.error if no display server is available

---

## `<file-level: game state>`

### Purpose
Defines shared mutable state for the game.

### Postconditions
- `score` is initialized to 0
- `ball_x` is initialized to SCREEN_W // 2 (400)
- `ball_y` is initialized to SCREEN_H // 2 (300)

### Invariants
- `score` is always >= 0

### Implementation Notes
- `ball_x`, `ball_y` are module-level globals, modified by reset_ball()
- `score` is a module-level global (not yet modified by any function in this file)

---

## `reset_ball() -> None`

### Purpose
Resets ball position to center of screen.

### Preconditions
- SCREEN_W and SCREEN_H are defined (set during initialization)

### Postconditions
- `ball_x` = SCREEN_W // 2
- `ball_y` = SCREEN_H // 2
- `score` is unchanged

### Invariants
- Pure positional reset — no score or other state changes

---

## `<file-level: main loop>`

### Purpose
Runs the game loop until the user closes the window.

### Preconditions
- Initialization block has run (screen, clock exist)
- Game state is initialized (ball_x, ball_y, score exist)

### Postconditions
- Game exits cleanly, pygame.quit() is called
- No resources leaked

### Implementation Notes
- Runs only when file is executed directly (`if __name__ == "__main__"`)
- Loop: poll events → call reset_ball() → tick clock at TICK_RATE
- Exits on pygame.QUIT event

### Failure Modes
- If initialization failed (no display), this block is never reached

---
```

Note: the spec is **shorter** than the code but captures everything needed to reimplement it correctly, including the file-level behavior.

---

## Phase 6: Package Output

After all `.engspec` files are validated, produce a standalone output package.

### What to include

Create a folder named `<project-name>-engspec/` containing:

1. **All `.engspec` files** — mirroring the source directory structure
2. **All non-code files from the repo** — copied verbatim, mirroring directory structure. These are files needed to regenerate a working project but that aren't source code:
   - Config files: `*.yaml`, `*.yml`, `*.toml`, `*.ini`, `*.cfg`, `*.conf`, `*.json`, `*.xml`
   - Documentation: `*.md`, `*.rst`, `*.txt` (README, CONTRIBUTING, CHANGELOG, etc.)
   - Build files: `Makefile`, `justfile`, `CMakeLists.txt`, `Dockerfile`, `docker-compose.yml`
   - CI/CD: `.github/workflows/*`, `.gitlab-ci.yml`, `.circleci/*`
   - Project metadata: `pyproject.toml`, `Cargo.toml`, `package.json`, `go.mod`, `go.sum`
   - Requirements/lockfiles: `requirements.txt`, `Cargo.lock`, `package-lock.json`, `poetry.lock`
   - Static assets: images, fonts, sounds, data files used by the project
   - Test fixtures and test data files (but NOT test source code — that gets regenerated from Test Strategy sections)
   - `.gitignore`, `.editorconfig`, `LICENSE`
3. **`project_context.md`** — the project context from Phase 1 (whether user-provided or auto-generated)
4. **`call_graph.md`** — the call graph analysis from Phase 2
5. **`test_coverage.md`** — the test coverage analysis from Phase 2
6. **`manifest.json`** — index of all files with validation status

**What NOT to include:**
- Source code files (`.py`, `.rs`, `.go`, `.c`, `.cpp`, `.js`, `.ts`, `.java`, etc.) — these are represented by `.engspec` files
- Build artifacts (`__pycache__/`, `target/`, `node_modules/`, `build/`, `dist/`)
- `.git/` directory
- IDE files (`.vscode/`, `.idea/`)
- Environment files with secrets (`.env` with real credentials — include `.env.example` if it exists)

### Directory structure

```
<project-name>-engspec/
├── project_context.md          # Phase 1 output
├── call_graph.md               # Phase 2 call graph
├── test_coverage.md            # Phase 2 test coverage analysis
├── manifest.json               # Index of all specs + non-code files
├── specs/                      # .engspec files mirroring source tree
│   ├── src/
│   │   ├── main.py.engspec
│   │   ├── utils.py.engspec
│   │   └── models/
│   │       └── player.py.engspec
│   └── lib/
│       └── physics.py.engspec
└── non_code/                   # Non-code files copied verbatim
    ├── README.md
    ├── LICENSE
    ├── pyproject.toml
    ├── requirements.txt
    ├── .gitignore
    ├── configs/
    │   └── settings.yaml
    ├── assets/
    │   └── sprite.png
    └── .github/
        └── workflows/
            └── ci.yml
```

### manifest.json format

```json
{
  "project": "<project-name>",
  "generated": "<ISO 8601 timestamp>",
  "source_repo": "<git URL or local path>",
  "languages": ["python"],
  "files": [
    {
      "spec": "specs/src/main.py.engspec",
      "source": "src/main.py",
      "language": "python",
      "status": "validated",
      "regeneration_count": 7,
      "regeneration_pass_rate": "5/5",
      "functions": 4,
      "file_level_sections": 2
    }
  ],
  "non_code_files": [
    {
      "path": "non_code/README.md",
      "original_path": "README.md",
      "type": "documentation"
    },
    {
      "path": "non_code/pyproject.toml",
      "original_path": "pyproject.toml",
      "type": "build"
    },
    {
      "path": "non_code/configs/settings.yaml",
      "original_path": "configs/settings.yaml",
      "type": "config"
    },
    {
      "path": "non_code/assets/sprite.png",
      "original_path": "assets/sprite.png",
      "type": "asset"
    }
  ],
  "summary": {
    "total_specs": 5,
    "validated": 5,
    "failed": 0,
    "total_functions": 23,
    "total_file_level_sections": 4,
    "total_regenerations": 31,
    "total_non_code_files": 6
  }
}
```

### Zip it

Compress the folder into `<project-name>-engspec.zip` and report the location.

```
pong-python-engspec.zip
├── project_context.md
├── call_graph.md
├── test_coverage.md
├── manifest.json
├── specs/
│   └── pong.py.engspec
└── non_code/
    ├── README.md
    ├── LICENSE
    ├── requirements.txt
    └── assets/
        └── beep.wav
```

### Why package separately

The `.engspec` package is a **standalone artifact**. It contains everything needed to:
- Understand the codebase without reading source code
- Re-implement any function from spec alone
- Assess test coverage gaps
- Feed into `engspec_tester` for adversarial analysis

It should be usable by someone who has never seen the original repo.
