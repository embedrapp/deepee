.PHONY: list lint doctor test image image-agent image-verifier image-smoke agent-network-up agent-network-down agent-network-smoke validate-reference validate-adequacy prepare-example verify-example report compile

AGENT_IMAGE ?= deepee-agent:1.2.0
VERIFIER_IMAGE ?= deepee-verifier:1.2.0
PLATFORM ?= linux/amd64
DOCKER ?= docker

list:
	python3 -m deepee.cli list-tasks

lint:
	python3 -m deepee.cli lint

doctor:
	python3 -m deepee.cli doctor --strict-tools --agent agents/codex-gpt-5.6-sol-xhigh.yaml

test: lint
	python3 -m unittest discover -s tests

prepare-example:
	python3 -m deepee.cli prepare-run --agent agents/codex-gpt-5.6-sol-xhigh.yaml --task deepee-repair-001

verify-example:
	python3 -m deepee.cli verify --container-image $(VERIFIER_IMAGE) --task deepee-repair-001 --run-dir runs/codex-gpt-5.6-sol-xhigh/deepee-repair-001/latest --output results/scored/example.json

image: image-agent image-verifier

image-agent:
	$(DOCKER) buildx build --load --pull=false --platform $(PLATFORM) --target agent --tag $(AGENT_IMAGE) --file docker/Dockerfile .

image-verifier:
	$(DOCKER) buildx build --load --pull=false --platform $(PLATFORM) --target verifier --tag $(VERIFIER_IMAGE) --file docker/Dockerfile .

image-smoke:
	$(DOCKER) run --rm $(AGENT_IMAGE) sh -ec 'test ! -e /opt/deepee/tasks; test ! -e /opt/deepee/validation; kicad-cli --version | grep -q 10.0.4; test -f /usr/share/kicad/symbols/Sensor_Temperature.kicad_sym; test -f /usr/share/kicad/footprints/Package_SO.pretty/MSOP-8_3x3mm_P0.65mm.kicad_mod; pio --version; codex --version'
	$(DOCKER) run --rm $(AGENT_IMAGE) codex exec --model gpt-5.6-sol --config 'model_reasoning_effort="xhigh"' --sandbox workspace-write --ephemeral --ignore-user-config --ignore-rules --json --help
	$(DOCKER) run --rm --network none $(VERIFIER_IMAGE) deepee doctor --strict-tools
	$(DOCKER) run --rm --network none $(VERIFIER_IMAGE) sh -ec 'test ! -e /opt/deepee/validation'
	$(DOCKER) run --rm --network none --user root --tmpfs /smoke:rw,size=256m $(VERIFIER_IMAGE) sh -ec 'kicad-cli sch export netlist --format kicadxml --output /smoke/power.xml /opt/deepee/tasks/schematic/deepee-sch-001/starter/artifacts/power-input.kicad_sch; mkdir -p /smoke/gerbers; kicad-cli pcb export gerbers --output /smoke/gerbers /opt/deepee/tasks/pcb/deepee-pcb-001/starter/artifacts/nrf24-adapter.kicad_pcb; test -s /smoke/power.xml; find /smoke/gerbers -type f -print -quit | grep -q .'
	$(DOCKER) run --rm --network none --user root --tmpfs /smoke:rw,size=2g $(VERIFIER_IMAGE) sh -ec 'cp -R /opt/deepee/tasks/firmware/deepee-fw-001/starter/artifacts/firmware /smoke/firmware; pio run --project-dir /smoke/firmware'
	AGENT_IMAGE=$(AGENT_IMAGE) DOCKER=$(DOCKER) ./scripts/agent-network.sh smoke

agent-network-up:
	AGENT_IMAGE=$(AGENT_IMAGE) DOCKER=$(DOCKER) ./scripts/agent-network.sh up

agent-network-down:
	AGENT_IMAGE=$(AGENT_IMAGE) DOCKER=$(DOCKER) ./scripts/agent-network.sh down

agent-network-smoke:
	AGENT_IMAGE=$(AGENT_IMAGE) DOCKER=$(DOCKER) ./scripts/agent-network.sh smoke

validate-reference:
	python3 -m validation.reference --container-image $(VERIFIER_IMAGE) --engine $(DOCKER)

validate-adequacy:
	python3 -m validation.adequacy --container-image $(VERIFIER_IMAGE) --engine $(DOCKER)

report:
	python3 -m deepee.cli report

compile:
	python3 -m compileall deepee harness validation docker/api_egress_proxy.py
