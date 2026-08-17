# Start benchmarking

## Prepare locally

These commands do not start Docker or install the hardware toolchain:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e .
make test
```

## Build on EC2

Use an x86_64 Ubuntu 24.04 host with at least 4 vCPUs, 16 GiB RAM, and 60 GiB free disk:

```bash
./scripts/bootstrap-ec2-ubuntu.sh
# Re-login once.
export CODEX_API_KEY='...'
./scripts/run-ec2-baseline.sh --task deepee-repair-001
```

To use a logged-in ChatGPT subscription instead, run `codex login --device-auth` on the host and invoke `./scripts/run-ec2-chatgpt-baseline.sh` with the same task arguments.

Use `--all-tasks` for the complete 48-task suite. The script runs repository tests, builds the two pinned images, proves the selected OpenAI authentication profile's restricted egress, performs offline verifier checks, verifies every private reference submission, runs doctor, and then starts one fresh attempt per selected task.

## Manual KiCad agent

Prepare a task bundle:

```bash
deepee benchmark \
  --agent agents/manual-kicad.yaml \
  --task deepee-sch-002 \
  --prepare-only
```

Give the generated `prompt_bundle.md` and run directory to the agent. After it finishes, verify that exact immutable run directory:

```bash
deepee verify \
  --container-image deepee-verifier:1.2.0 \
  --task deepee-sch-002 \
  --run-dir '<printed-run-directory>' \
  --output results/scored/manual-sch-002.json

deepee package-run \
  --run-dir '<printed-run-directory>' \
  --output results/artifacts/manual-sch-002.zip

deepee report
```

Do not retry inside the same run directory. Do not publish host-only or missing-tool verification as benchmark evidence.
