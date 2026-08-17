# Security policy

Report credential exposure, sandbox escape, evaluator-data leakage into the agent image, or restricted-network bypass privately to the repository maintainers before opening a public issue.

Benchmark prompts and submissions are untrusted input. Verification runs without network access, mounts submissions read-only, and writes only to its dedicated verification workspace. Never add shell interpolation of submission-controlled values or mount the operator's Codex home into the verifier.
