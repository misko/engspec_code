# Create Input Prompt

You are analyzing a code repository to generate an `input.md` file that describes the project for specification generation.

## Your Task

Read the repository contents and produce a structured `input.md` with these sections:

1. **Project: <name>** - The project name
2. **Description** - What the repository does, its purpose, key abstractions, architecture overview
3. **Test Environment Setup** - How to install dependencies, set up the dev environment
4. **Running Tests** - How to run the test suite, specific commands, flags, config files
5. **Examples** - Example usage of the main APIs/CLIs
6. **Notes** - Any other context: known issues, conventions, important directories

## Sources to Examine

- README.md, CONTRIBUTING.md
- Build files: pyproject.toml, Cargo.toml, package.json, CMakeLists.txt, go.mod
- CI configs: .github/workflows/, .gitlab-ci.yml
- Makefile, justfile
- Test directories and test configuration
- Main source code structure
- Git history (recent commits)

## Output Format

Produce a complete markdown document following the sections above. Be thorough but concise.
