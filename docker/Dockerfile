FROM kicad/kicad:10.0.4@sha256:770e2fa006695077b5ba218742d5c3137896af91257b2ca971243fa56b01bb86 AS toolchain

ARG PLATFORMIO_VERSION=6.1.19
ARG PYYAML_VERSION=6.0.3
ARG JSONSCHEMA_VERSION=4.25.1

USER root
ENV DEBIAN_FRONTEND=noninteractive
ENV PIP_BREAK_SYSTEM_PACKAGES=1
ENV PLATFORMIO_CORE_DIR=/opt/platformio

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    git \
    python3 \
    python3-pip \
    python3-venv \
    make \
    gcc \
    g++ \
    unzip \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m pip install --no-cache-dir --ignore-installed \
    "PyYAML==${PYYAML_VERSION}" \
    "jsonschema==${JSONSCHEMA_VERSION}" \
    "platformio==${PLATFORMIO_VERSION}"

COPY docker/platformio-preload /tmp/platformio-preload
RUN mkdir -p "${PLATFORMIO_CORE_DIR}" \
    && pio pkg install --project-dir /tmp/platformio-preload \
    && pio run --project-dir /tmp/platformio-preload \
    && rm -rf /tmp/platformio-preload

RUN useradd --create-home --shell /bin/bash benchmark \
    && mkdir -p /work \
        /root/.config/kicad/10.0 \
        /home/benchmark/.config/kicad/10.0 \
    && cp /usr/share/kicad/template/sym-lib-table /root/.config/kicad/10.0/ \
    && cp /usr/share/kicad/template/fp-lib-table /root/.config/kicad/10.0/ \
    && cp /usr/share/kicad/template/sym-lib-table /home/benchmark/.config/kicad/10.0/ \
    && cp /usr/share/kicad/template/fp-lib-table /home/benchmark/.config/kicad/10.0/ \
    && chown -R benchmark:benchmark /work /home/benchmark "${PLATFORMIO_CORE_DIR}"

# The authoring image intentionally contains no benchmark tasks or verifier code.
# It has network access during a run because Codex must reach the OpenAI API.
FROM toolchain AS agent

ARG CODEX_VERSION=0.144.2
RUN apt-get update \
    && apt-get install -y --no-install-recommends nodejs npm \
    && npm install --global "@openai/codex@${CODEX_VERSION}" \
    && mkdir -p /root/.codex \
    && rm -rf /var/lib/apt/lists/* /root/.npm
COPY docker/api_egress_proxy.py /usr/local/bin/deepee-api-egress-proxy

USER benchmark
WORKDIR /work
CMD ["/bin/bash"]

# The verifier image contains the benchmark and runs with networking disabled.
# It intentionally does not contain Codex or any agent credentials.
FROM toolchain AS verifier

WORKDIR /opt/deepee
COPY pyproject.toml README.md LICENSE THIRD_PARTY_NOTICES.md ./
COPY benchmark.yaml ./benchmark.yaml
COPY deepee ./deepee
COPY tasks ./tasks
COPY agents/AGENT_CONTEXT.md ./agents/AGENT_CONTEXT.md
COPY docker/tool-versions.lock ./docker/tool-versions.lock
RUN python3 -m pip install --no-cache-dir --no-deps .

USER benchmark
WORKDIR /work
CMD ["/bin/bash"]
