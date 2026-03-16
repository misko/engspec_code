Read the engspec tester prompt and format spec for your instructions:

1. Read `engspec_format.md` in this repository for the `.engspec` format specification, round output format, and analysis report template.
2. Read `engspec_tester_prompt.md` in this repository for the complete workflow.

Then execute the workflow with the following user input:

$ARGUMENTS

If a single path is provided, treat it as the engspec package path. If two paths are provided, the first is the engspec package and the second is the source repo.

If no arguments are provided, ask the user for:
- The engspec package path (required)
- The source repo path (optional, recommended for spec+source mode)
