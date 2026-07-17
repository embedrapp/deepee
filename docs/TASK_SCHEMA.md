# Task schema

Each task contains:

```text
tasks/<suite>/<task-id>/
  manifest.yaml
  prompt.md
  expected_artifacts.yaml
  SOURCE.md
  starter/
  verifier/                 # optional verifier-owned tests
```

Example manifest:

```yaml
id: deepee-pcb-001
suite: pcb
difficulty: medium
timeout_minutes: 60
required_tools: [kicad-cli]
submission_paths: [artifacts/board.kicad_pcb]
required_artifacts:
  - {path: artifacts/board.kicad_pcb, kind: file}
checks:
  - type: artifact_presence
    name: board_exists
  - type: kicad_pcb_structure
    name: fixed_board_contract
    board: artifacts/board.kicad_pcb
  - type: kicad_drc
    name: clean_drc
    board: artifacts/board.kicad_pcb
```

All paths are relative to the fresh run directory. Absolute paths and `..` are rejected. Deprecated weighted-scoring and verification-track fields are rejected by lint.

## Checks

- `artifact_presence`: required files, directories, or globs exist.
- `starter_integrity`: protected starter APIs/configuration are byte-identical.
- `c_unit_tests`: submitted C is compiled directly with verifier-owned tests.
- `firmware_build`: a declared PlatformIO project builds and produces an ELF.
- `kicad_schematic_structure`: native schematic symbols, references, values, footprints, and named nets match the fixed contract.
- `kicad_netlist_contract`: KiCad exports a fresh XML netlist; required component values/footprints and pin-to-net mappings are checked.
- `kicad_pcb_structure`: native board layers, outline, footprints, pad nets, tracks, vias, and zones match the fixed contract.
- `kicad_erc` / `kicad_drc`: KiCad CLI runs with errors and warnings enabled and exits nonzero for violations.

Every declared check is mandatory. The verifier returns `score: 1.0` only when all pass, otherwise `score: 0.0`.

Hardware contracts specify exact components and interface nets but intentionally do not prescribe full golden netlists, placement coordinates, or trace geometry.
