from .artifact import run_artifact_presence
from .c_tests import run_c_unit_tests
from .firmware import run_firmware_build
from .kicad import run_kicad_drc, run_kicad_erc
from .kicad_netlist import run_kicad_netlist_contract
from .kicad_structural import run_kicad_pcb_structure, run_kicad_schematic_structure
from .integrity import run_starter_integrity


CHECKS = {
    "artifact_presence": run_artifact_presence,
    "c_unit_tests": run_c_unit_tests,
    "firmware_build": run_firmware_build,
    "kicad_drc": run_kicad_drc,
    "kicad_erc": run_kicad_erc,
    "kicad_netlist_contract": run_kicad_netlist_contract,
    "kicad_pcb_structure": run_kicad_pcb_structure,
    "kicad_schematic_structure": run_kicad_schematic_structure,
    "starter_integrity": run_starter_integrity,
}
