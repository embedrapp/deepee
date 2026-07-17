# EC2 execution handoff

DeepEE does not require a local VM on the development laptop. Build and execute the benchmark later on an x86_64 Ubuntu EC2 host.

## Host envelope

Use Ubuntu 24.04 on `x86_64` with at least:

- 4 vCPUs;
- 16 GiB RAM;
- 60 GiB free root-volume space;
- outbound HTTPS for image/package installation and the Codex API.

The benchmark images are locked to `linux/amd64`, so an x86_64 instance avoids emulation. The verifier itself runs without network access.

## Bootstrap

After cloning the repository:

```bash
./scripts/bootstrap-ec2-ubuntu.sh
```

Log out and back in once so Docker group membership applies. The script installs only host prerequisites; all KiCad, compiler, PlatformIO, and Codex versions live in the repository's Docker stages.

## Authenticate and run

Use a short-lived API key. ChatGPT-account auth files are intentionally unsupported because benchmark agent egress is restricted to `api.openai.com:443`:

```bash
export CODEX_API_KEY='...'
./scripts/run-ec2-baseline.sh --task deepee-repair-001
```

For the full baseline:

```bash
./scripts/run-ec2-baseline.sh --all-tasks
```

The run script creates a Python virtual environment, runs lightweight harness tests, builds both pinned images, executes image and network smoke checks, validates one private known-good submission for every discovered task, runs doctor, and then starts exactly one benchmark attempt per selected task. Any failed reference ERC, DRC, native test, target build, OpenAI-only proxy check, or blocked-egress check stops the run before credentials are used.

## Prebuilt release images

Tagging a public release with `v*` runs `release-images.yml`, which publishes separate agent and verifier images to GHCR and records their content digests as a workflow artifact. To use prebuilt images instead of local builds:

```bash
export DEEPEE_AGENT_IMAGE='ghcr.io/OWNER/REPOSITORY-agent:VERSION'
export DEEPEE_VERIFIER_IMAGE='ghcr.io/OWNER/REPOSITORY-verifier:VERSION'
docker pull "$DEEPEE_AGENT_IMAGE"
docker pull "$DEEPEE_VERIFIER_IMAGE"
```

Then run the smoke and network setup with matching image variables before invoking `deepee benchmark`:

```bash
make image-smoke AGENT_IMAGE="$DEEPEE_AGENT_IMAGE" VERIFIER_IMAGE="$DEEPEE_VERIFIER_IMAGE"
make agent-network-up AGENT_IMAGE="$DEEPEE_AGENT_IMAGE"
trap 'make agent-network-down' EXIT
deepee benchmark \
  --agent agents/codex-gpt-5.6-sol-xhigh.yaml \
  --all-tasks \
  --verification-image "$DEEPEE_VERIFIER_IMAGE"
```

Every run records the effective image names, immutable image IDs, and Docker engine versions. Export `DEEPEE_AGENT_IMAGE` as well so the agent configuration uses the pulled image rather than its default local tag.

Do not reuse a working directory for another first attempt. Preserve `runs/`, `results/scored/`, and the generated leaderboard output together.
