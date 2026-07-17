# Private reference validation

This directory contains one known-good submission for every benchmark task. It is used only as a release gate: the validation harness overlays each solution onto a fresh starter and verifies it with the same offline, read-only submission mount used for real scores.

`validation/` is excluded from the Docker build context and is not copied into either benchmark image. It must never be mounted into an agent run. The CI and EC2 release gates run it only after the agent and verifier images have been built.

Regenerate the KiCad fixtures only when their task contracts change:

```bash
python -m pip install -r validation/requirements.txt
KICAD_SYMBOL_DIR=/usr/share/kicad/symbols \
  python validation/generate_hardware_fixtures.py
```

Validate all reference submissions on the Ubuntu x86_64 benchmark host:

```bash
python -m validation.reference --container-image deepee-verifier:1.1.0
```
