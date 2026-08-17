#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${repo_root}"
agent_config="${DEEPEE_AGENT_CONFIG:-agents/codex-gpt-5.6-sol-xhigh.yaml}"

if [[ "$(uname -m)" != "x86_64" ]]; then
  echo "DeepEE release images target linux/amd64; use an x86_64 EC2 instance." >&2
  exit 2
fi
if ! docker info >/dev/null 2>&1; then
  echo "Docker is unavailable. Run bootstrap-ec2-ubuntu.sh, then log out and back in." >&2
  exit 2
fi
if ! docker buildx version >/dev/null 2>&1; then
  echo "Docker buildx is unavailable." >&2
  exit 2
fi

if [[ "${DEEPEE_CHATGPT_AUTH:-0}" == "1" ]]; then
  if [[ ! -s "${CODEX_HOME:-${HOME}/.codex}/auth.json" ]]; then
    echo "Codex ChatGPT authentication is missing. Run codex login --device-auth first." >&2
    exit 2
  fi
elif [[ -z "${CODEX_API_KEY:-}" ]]; then
  echo "Set CODEX_API_KEY. The restricted agent network supports API-key authentication only." >&2
  exit 2
fi

python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .

make test
make image
make image-smoke
make validate-reference
make validate-adequacy
DEEPEE_CHATGPT_AUTH="${DEEPEE_CHATGPT_AUTH:-0}" make agent-network-up
trap 'make agent-network-down >/dev/null 2>&1 || true' EXIT
python3 -m deepee.cli doctor --strict-tools --agent "${agent_config}"

if [[ "$#" -eq 0 ]]; then
  set -- --task deepee-repair-001
fi

deepee benchmark \
  --agent "${agent_config}" \
  "$@"
