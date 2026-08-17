# Contributing to DeepEE

Keep changes scoped, reproducible, and reviewable. Do not commit credentials, VM keys, Codex authentication data, local editor state, generated run directories, or private operator documentation.

## Task changes

Every task must include a prompt, starter, expected-artifact declaration, provenance file, manifest v2 requirement contract, known-good solution, and one adequacy mutant per critical requirement. Pass/fail requirements must be stated in the prompt. Do not use golden-file equality for a design when multiple valid implementations exist.

Run before opening a pull request:

```bash
make test
make compile
make image
make image-smoke
make validate-reference
make validate-adequacy
```

The last three commands require the pinned x86-64 container environment.

## Git history

Create a focused feature branch, use conventional commit messages, and keep generated output out of commits unless it is an intentional published artifact. Pull requests must explain the contract change, affected tasks, negative fixtures, and exact verification performed. Merge only a revision that passes CI and independent review.
