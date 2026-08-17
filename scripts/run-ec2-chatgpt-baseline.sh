#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${repo_root}"

export DEEPEE_AGENT_CONFIG="agents/codex-gpt-5.6-sol-xhigh-chatgpt.yaml"
export DEEPEE_CHATGPT_AUTH=1

exec ./scripts/run-ec2-baseline.sh "$@"
