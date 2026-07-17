#!/usr/bin/env bash
set -euo pipefail

if [[ "$(uname -m)" != "x86_64" ]]; then
  echo "DeepEE release images target linux/amd64; use an x86_64 EC2 instance." >&2
  exit 2
fi

if [[ ! -r /etc/os-release ]]; then
  echo "This bootstrap supports Ubuntu hosts with /etc/os-release." >&2
  exit 2
fi

. /etc/os-release
if [[ "${ID:-}" != "ubuntu" ]]; then
  echo "This bootstrap supports Ubuntu; found ${ID:-unknown}." >&2
  exit 2
fi

sudo apt-get update
sudo apt-get install -y ca-certificates curl git gcc make python3 python3-venv

if ! command -v docker >/dev/null 2>&1 || ! docker buildx version >/dev/null 2>&1; then
  sudo install -m 0755 -d /etc/apt/keyrings
  sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
  sudo chmod a+r /etc/apt/keyrings/docker.asc
  architecture="$(dpkg --print-architecture)"
  codename="${UBUNTU_CODENAME:-${VERSION_CODENAME}}"
  echo "deb [arch=${architecture} signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu ${codename} stable" \
    | sudo tee /etc/apt/sources.list.d/docker.list >/dev/null
  sudo apt-get update
  sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin
fi

sudo systemctl enable --now docker
sudo usermod -aG docker "${USER}"

echo "EC2 bootstrap complete. Log out and back in once so Docker group membership takes effect."
echo "Then run: ./scripts/run-ec2-baseline.sh --task deepee-repair-001"
