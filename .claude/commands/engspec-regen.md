Read the engspec regeneration prompt and format spec for your instructions:

1. Read `engspec_format.md` in this repository for the `.engspec` format specification and manifest schema.
2. Read `engspec_to_code_prompt.md` in this repository for the complete workflow.

Then execute the workflow with the following user input:

$ARGUMENTS

If a single path is provided, treat it as the engspec package path and regenerate into a sibling directory named `<project>-regen/`. If two paths are provided, the first is the engspec package and the second is the output directory.

If no arguments are provided, ask the user for:
- The engspec package path (required)
- The output directory for the regenerated codebase
- For partial packages: the existing codebase path
