# Public run protocol

## One attempt

1. Check out an immutable benchmark revision and select the pinned agent/verifier images.
2. Pass repository tests, image and restricted-egress smoke checks, all private reference submissions, and `deepee doctor` on the execution host.
3. Create a fresh run directory with the task prompt and starter tree.
4. Start one agent process and stop it at the task timeout.
5. Freeze the run directory and verify it in the offline verifier image.
6. Keep the scored JSON and deterministic evidence ZIP, including failed attempts.
7. Regenerate `leaderboard/results.json` with `deepee report`.

## Fair comparison

- Compared agents receive the same prompt, starter files, timeout, resource limits, and verifier revision.
- A timeout, crash, or nonzero automated-agent exit fails the task.
- Every task check must pass; there is no partial credit.
- The first publishable attempt for an agent configuration, benchmark hash, immutable agent/verifier image IDs, and task is the only attempt counted by Pass@1.
- Pass@1 is reported only after that exact cohort has attempted every task declared by its verifier; incomplete cohorts show a null aggregate and list the missing tasks.
- Hardware deliverables must be native KiCad 10 files. Vendor-neutral or lossy exchange exports are not accepted in version 1.
- Human changes after the attempt starts make the run a different evaluation condition and must not be reported as an autonomous baseline.

## Isolation and provenance

The agent image contains authoring tools but not `tasks/`, verifier code, or reference solutions. During an automated Codex attempt it has no direct internet route: an internal Docker network reaches a dedicated CONNECT proxy. The API-key profile accepts only `api.openai.com:443`; the ChatGPT-subscription profile additionally accepts `auth.openai.com:443` and `chatgpt.com:443`. Both reject every other authority. The selected agent configuration, active proxy profile, authentication mode, and exact allowlist must agree and are recorded in run evidence. Manual/external agents are recorded as `external_uncontrolled` with unknown egress rather than making an isolation claim DeepEE cannot enforce. The verifier receives the frozen submission as a read-only bind mount and writes build/report evidence to a separate temporary mount. It runs with networking disabled, all Linux capabilities dropped, and a temporary home.

A publishable record keeps run timestamps and IDs, agent/model/effort, effective network policy, task and benchmark hashes, prompt and agent-config hashes, submission/artifact hashes, image IDs, tool versions, process result, wall time, and token usage when the runner reports it.

When an agent config declares public token prices, the run also records a cached-aware API-equivalent estimate for that benchmark request. Cached input is subtracted from total input before the uncached rate is applied. ChatGPT subscription attempts still have no per-task token invoice, so the estimate records `actual_subscription_charge_usd: null`. Codex CLI exposes aggregate turn usage rather than each underlying API request; cache-write charges and request-specific long-context multipliers therefore remain explicitly excluded from the estimate.

Host verification and `--allow-missing-tools` are development checks and are never publishable.
