#!/usr/bin/env bash
set -euo pipefail

docker_cmd="${DOCKER:-docker}"
agent_image="${AGENT_IMAGE:-deepee-agent:1.2.0}"
network="deepee-agent-internal"
proxy_name="deepee-api-egress"
proxy_url="http://${proxy_name}:3128"

down() {
  "${docker_cmd}" rm --force "${proxy_name}" >/dev/null 2>&1 || true
  "${docker_cmd}" network rm "${network}" >/dev/null 2>&1 || true
}

up() {
  down
  "${docker_cmd}" network create --internal "${network}" >/dev/null
  "${docker_cmd}" run --detach --name "${proxy_name}" --network bridge \
    --env "DEEPEE_CHATGPT_AUTH=${DEEPEE_CHATGPT_AUTH:-0}" \
    "${agent_image}" python3 /usr/local/bin/deepee-api-egress-proxy >/dev/null
  "${docker_cmd}" network connect --alias "${proxy_name}" "${network}" "${proxy_name}"
  for _ in $(seq 1 50); do
    if "${docker_cmd}" exec "${proxy_name}" python3 -c \
      'import socket; socket.create_connection(("127.0.0.1", 3128), 1).close()' >/dev/null 2>&1; then
      return
    fi
    sleep 0.1
  done
  echo "DeepEE API egress proxy did not become ready." >&2
  down
  return 1
}

smoke() {
  trap down EXIT
  up

  status="$("${docker_cmd}" run --rm --network "${network}" \
    --env "HTTPS_PROXY=${proxy_url}" --env "NO_PROXY=" \
    "${agent_image}" curl --connect-timeout 5 --max-time 10 --silent --show-error --output /dev/null \
    --write-out '%{http_code}' https://api.openai.com/v1/models)"
  if [[ "${status}" != "401" ]]; then
    echo "OpenAI API egress returned HTTP ${status}; expected 401 without credentials." >&2
    return 1
  fi

  if [[ "${DEEPEE_CHATGPT_AUTH:-0}" == "1" ]]; then
    for authority in auth.openai.com chatgpt.com; do
      status="$("${docker_cmd}" run --rm --network "${network}" \
        --env "HTTPS_PROXY=${proxy_url}" --env "NO_PROXY=" \
        "${agent_image}" curl --connect-timeout 5 --max-time 10 --silent --show-error --output /dev/null \
        --write-out '%{http_code}' "https://${authority}/")"
      if [[ "${status}" == "000" ]]; then
        echo "ChatGPT subscription egress could not reach ${authority}:443." >&2
        return 1
      fi
    done
  elif "${docker_cmd}" run --rm --network "${network}" \
    --env "HTTPS_PROXY=${proxy_url}" --env "NO_PROXY=" \
    "${agent_image}" curl --connect-timeout 5 --max-time 10 --silent --show-error \
    https://auth.openai.com/ >/dev/null 2>&1; then
    echo "API-key profile unexpectedly reached auth.openai.com." >&2
    return 1
  fi

  if "${docker_cmd}" run --rm --network "${network}" \
    --env "HTTPS_PROXY=${proxy_url}" --env "NO_PROXY=" \
    "${agent_image}" curl --connect-timeout 5 --max-time 10 --fail --silent --show-error https://github.com/ >/dev/null 2>&1; then
    echo "Allowlisted proxy unexpectedly reached github.com." >&2
    return 1
  fi
  if "${docker_cmd}" run --rm --network "${network}" \
    "${agent_image}" curl --connect-timeout 5 --max-time 10 --noproxy '*' --fail --silent --show-error https://github.com/ >/dev/null 2>&1; then
    echo "Internal agent network unexpectedly allowed direct internet egress." >&2
    return 1
  fi
}

case "${1:-}" in
  up) up ;;
  down) down ;;
  smoke) smoke ;;
  *) echo "usage: $0 {up|down|smoke}" >&2; exit 2 ;;
esac
