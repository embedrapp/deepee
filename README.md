# DeepEE

DeepEE is a small benchmark for AI agents doing embedded firmware and KiCad engineering. An agent receives a prompt plus starter files, edits a fresh working directory, and submits ordinary source files. An offline verifier checks the result. Conversation quality and screenshots do not count.

## Scope

Version 1.1 has twelve tasks:

| Task | Agent work | Pass gate |
|---|---|---|
| `deepee-repair-001` | Repair rollover-unsafe C scheduler code | Protected API + native C tests |
| `deepee-repair-002` | Repair a wrapped byte ring buffer | Protected API + native C tests |
| `deepee-repair-003` | Repair overflow-unsafe ADC scaling | Protected API + native C tests |
| `deepee-fw-001` | Complete an ESP32-S2 I²C recovery policy | Native C tests + PlatformIO build |
| `deepee-fw-002` | Implement SHT3x CRC and measurement decoding | Native C tests + PlatformIO build |
| `deepee-fw-003` | Implement BME280 integer temperature compensation | Native C tests + PlatformIO build |
| `deepee-fw-004` | Implement Modbus RTU CRC-16 | Native C tests + PlatformIO build |
| `deepee-fw-005` | Decode signed MCP9808 temperature registers | Native C tests + PlatformIO build |
| `deepee-sch-001` | Review and repair a broken KiCad schematic | Fixed component/net contract + ERC |
| `deepee-pcb-001` | Finish routing an nRF24L01 adapter | Fixed footprint/pad contract + DRC |
| `deepee-sch-002` | Design an MCP9808 breakout schematic from scratch | Exported netlist contract + ERC |
| `deepee-pcb-002` | Design and route the breakout PCB from scratch | Footprint/pad/outline contract + DRC |

The tasks are compact adaptations of real bug reports, open-source boards, official KiCad QA material, and published breakout use cases. Provenance is recorded in each task's `SOURCE.md` and summarized in [docs/TASK_SOURCES.md](docs/TASK_SOURCES.md).

## What is verified

Every listed check is mandatory. A task score is binary:

```text
all checks pass -> 1
anything fails  -> 0
```

The primary aggregate is Pass@1: the fraction of tasks passed on an agent's first publishable attempt. The verifier checks exact required parts and pin/pad nets, but it does not compare a whole schematic netlist, component placement, or trace geometry with a golden answer. KiCad performs the final ERC/DRC gate.

This is deliberately a KiCad-native benchmark, not a tool-agnostic EDA benchmark. An AI system may be compared if it can produce the required native KiCad 10 artifacts. Altium- or EasyEDA-only outputs are out of scope because silently converting them would weaken the assurance and make the comparison misleading.

Firmware is verified by native unit tests and a real target build. Version 1.1 does not claim runtime peripheral, timing, analog, thermal, EMI, or fabrication signoff; Renode and circuit simulation are intentionally deferred.

## Lightweight local preparation

No VM, Colima instance, Docker image, KiCad install, or PlatformIO install is needed on the development laptop. The repository checks use Python and a host C compiler only:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e .
make test
```

The Dockerfiles and scripts are deployment material for a later x86_64 Ubuntu EC2 run. They are not started by the commands above.

## EC2 execution

On an Ubuntu 24.04 x86_64 host:

```bash
./scripts/bootstrap-ec2-ubuntu.sh
# Log out and back in once for Docker group membership.
export CODEX_API_KEY='...'
./scripts/run-ec2-baseline.sh --all-tasks
```

The deployment builds separate `deepee-agent:1.1.0` and `deepee-verifier:1.1.0` images. The agent image has KiCad 10.0.4, PlatformIO 6.1.19, compilers, and Codex but no benchmark tasks or verifier code. Agent runs use an internal-only Docker network whose CONNECT proxy permits only `api.openai.com:443`; the host smoke gate proves both that route and blocked GitHub/direct egress. Verification runs without any network or agent credentials. Before a baseline starts, the Ubuntu host also proves one private reference submission for every task against that same verifier image. See [docs/EC2.md](docs/EC2.md) and [docs/RUN_PROTOCOL.md](docs/RUN_PROTOCOL.md).

For a manual external agent that uses KiCad:

```bash
deepee benchmark \
  --agent agents/manual-kicad.yaml \
  --task deepee-pcb-001 \
  --prepare-only

deepee verify \
  --container-image deepee-verifier:1.1.0 \
  --task deepee-pcb-001 \
  --run-dir '<printed-run-directory>' \
  --output results/scored/external-pcb-run.json
```

DeepEE's original code and fixtures are MIT licensed. The KiCad-derived schematic starter identified in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) retains its GPLv3 license. Compare leaderboard results only when the benchmark and task hashes match.
