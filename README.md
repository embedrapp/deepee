# DeepEE

DeepEE is a small benchmark for AI agents doing embedded firmware and KiCad engineering. An agent receives a prompt plus starter files, edits a fresh working directory, and submits ordinary source files. An offline verifier checks the result. Conversation quality and screenshots do not count.

## Scope

Version 1.1 has 48 tasks: 12 in each engineering category.

| Category | Task IDs | Topics | Pass gate |
|---|---|---|---|
| Firmware | `deepee-fw-001`–`012` | I²C recovery; SHT3x, BME280, MCP9808, INA219, BMP280, ADS1115, DS18B20, SCD4x, PCA9685, and MAX31855 drivers; Modbus CRC | Protected API + native C tests + PlatformIO build |
| Code repair | `deepee-repair-001`–`012` | Scheduler rollover, ring buffers, ADC scaling, SLIP, MQTT, UTF-8, CBOR, PPP FCS, HTTP chunks, Base64, Modbus CRC, and wrap-safe tick timing | Protected API + native C tests |
| Schematics | `deepee-sch-001`–`012` | Power-input repair, MCP9808, INA219, ADS1115, BMP280, AP2112, USB-C sink, RS-485, CAN, I²C level shifting, microSD, and NE555 | Exact component/pin-net contract + exported netlist + ERC |
| PCB | `deepee-pcb-001`–`012` | nRF24L01, MCP9808, and the same ten researched interface circuits used by the schematic set | Exact footprint/pad/outline contract + fully routed nets + DRC |

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
