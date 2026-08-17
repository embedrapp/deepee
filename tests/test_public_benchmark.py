from __future__ import annotations

import importlib.util
import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import yaml

from deepee.archive import package_run
from deepee.checks.kicad import run_kicad_drc, run_kicad_erc
from deepee.checks.kicad_netlist import run_kicad_netlist_contract
from deepee.checks.kicad_structural import run_kicad_pcb_structure
from deepee.runner import _parse_jsonl, prepare_run
from deepee.task import iter_tasks, resolve_task
from deepee.verifier import verify_task
from validation.reference import SOLUTIONS, assemble_reference_run


REPO_ROOT = Path(__file__).resolve().parents[1]


CORRECT_SCHEDULER = r'''#include "scheduler.h"

#include <stdint.h>

void scheduler_init(PeriodicScheduler *scheduler, uint32_t now_ms, uint32_t period_ms) {
    scheduler->period_ms = period_ms;
    scheduler->next_due_ms = now_ms + period_ms;
}

bool scheduler_due(const PeriodicScheduler *scheduler, uint32_t now_ms) {
    return (int32_t)(now_ms - scheduler->next_due_ms) >= 0;
}

void scheduler_advance(PeriodicScheduler *scheduler, uint32_t now_ms) {
    do {
        scheduler->next_due_ms += scheduler->period_ms;
    } while (scheduler_due(scheduler, now_ms));
}
'''


class PublicBenchmarkTests(unittest.TestCase):
    def test_release_contract_is_binary_kicad_10_and_forty_eight_tasks(self) -> None:
        release = yaml.safe_load((REPO_ROOT / "benchmark.yaml").read_text(encoding="utf-8"))
        self.assertEqual(release["version"], "1.1.0")
        self.assertEqual(release["toolchain"]["kicad"], "10.0.4")
        self.assertEqual(release["toolchain"]["platformio"], "6.1.19")
        self.assertEqual(release["score_policy"]["primary_metric"], "pass_at_1")
        self.assertEqual(release["score_policy"]["task_result"], "all_checks_must_pass")
        self.assertEqual(release["network_policy"]["agent_egress"], ["api.openai.com:443"])
        self.assertEqual(release["network_policy"]["verifier_egress"], [])
        expected = {
            f"deepee-{category}-{number:03d}"
            for category in ("repair", "fw", "sch", "pcb")
            for number in range(1, 13)
        }
        self.assertEqual({task.id for task in iter_tasks(REPO_ROOT)}, expected)

    def test_runner_is_containerized_without_mounting_user_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, mock.patch(
            "deepee.runner._container_image_id", return_value="sha256:test"
        ), mock.patch("deepee.runner._container_command_version", return_value="codex test"), mock.patch(
            "deepee.runner._command_version", return_value="test"
        ):
            metadata = prepare_run(
                REPO_ROOT / "agents" / "codex-gpt-5.6-sol-xhigh.yaml",
                "deepee-repair-001",
                Path(tmp) / "runs",
                REPO_ROOT,
            )
        self.assertEqual(metadata["command"][0], "docker")
        self.assertIn("--interactive", metadata["command"])
        self.assertIn("deepee-agent:1.1.0", metadata["command"])
        self.assertEqual(metadata["container"]["verification_image"], "deepee-verifier:1.1.0")
        self.assertFalse(metadata["container"]["mount_codex_home"])
        self.assertFalse(metadata["container"]["mount_codex_auth"])
        self.assertEqual(metadata["container"]["network"], "deepee-agent-internal")
        self.assertIn("HTTPS_PROXY=http://deepee-api-egress:3128", metadata["command"])
        self.assertIn("NO_PROXY=", metadata["command"])
        self.assertFalse(any("dst=/root/.codex," in part for part in metadata["command"]))
        self.assertEqual(metadata["inner_command"][-1], "-")
        self.assertNotIn("verification_track", metadata)

    def test_evidence_archive_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = root / "run"
            (run_dir / "artifacts").mkdir(parents=True)
            (run_dir / "prompt_bundle.md").write_text("prompt\n", encoding="utf-8")
            (run_dir / "artifacts" / "result.txt").write_text("artifact\n", encoding="utf-8")
            first = package_run(run_dir, root / "first.zip")
            second = package_run(run_dir, root / "second.zip")
            self.assertEqual(first["sha256"], second["sha256"])
            self.assertEqual(first["file_count"], 2)

    def test_codex_jsonl_usage_is_recorded(self) -> None:
        output = "\n".join([
            json.dumps({"type": "thread.started", "thread_id": "thread-1"}),
            json.dumps({"type": "turn.completed", "usage": {"input_tokens": 20, "output_tokens": 7}}),
        ])
        parsed = _parse_jsonl(output)
        self.assertEqual(parsed["thread_id"], "thread-1")
        self.assertEqual(parsed["usage"], {"input_tokens": 20, "output_tokens": 7})

    @unittest.skipUnless(shutil.which("cc"), "C compiler required")
    def test_repair_solution_passes_binary_verifier(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            metadata = prepare_run(
                REPO_ROOT / "agents" / "manual-kicad.yaml",
                "deepee-repair-001",
                Path(tmp) / "runs",
                REPO_ROOT,
            )
            run_dir = Path(metadata["run_dir"])
            (run_dir / "firmware" / "src" / "scheduler.c").write_text(CORRECT_SCHEDULER, encoding="utf-8")
            payload = verify_task("deepee-repair-001", run_dir, root=REPO_ROOT)
            self.assertTrue(payload["passed"], payload)
            self.assertEqual(payload["score"], 1.0)
            self.assertEqual(payload["failures"], [])
            self.assertFalse(payload["publishable"])
            self.assertTrue(payload["metadata"]["hashes"]["submission"])

    @unittest.skipUnless(shutil.which("cc"), "C compiler required")
    def test_protected_contract_tampering_fails_whole_task(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            metadata = prepare_run(
                REPO_ROOT / "agents" / "manual-kicad.yaml",
                "deepee-repair-001",
                Path(tmp) / "runs",
                REPO_ROOT,
            )
            run_dir = Path(metadata["run_dir"])
            (run_dir / "firmware" / "src" / "scheduler.c").write_text(CORRECT_SCHEDULER, encoding="utf-8")
            header = run_dir / "firmware" / "src" / "scheduler.h"
            header.write_text(header.read_text(encoding="utf-8") + "\n/* changed */\n", encoding="utf-8")
            payload = verify_task("deepee-repair-001", run_dir, root=REPO_ROOT)
            self.assertFalse(payload["passed"])
            self.assertEqual(payload["score"], 0.0)
            self.assertIn("scheduler_contract_unchanged", payload["failures"])

    def test_nrf24_starter_has_only_the_intended_routing_failures(self) -> None:
        task_dir = REPO_ROOT / "tasks" / "pcb" / "deepee-pcb-001"
        check = yaml.safe_load((task_dir / "manifest.yaml").read_text(encoding="utf-8"))["checks"][1]
        result = run_kicad_pcb_structure(
            check,
            SimpleNamespace(id="deepee-pcb-001"),
            (task_dir / "starter").resolve(),
            {},
        )
        failed = {
            item["name"]
            for item in result["details"]["subchecks"]
            if not item["passed"]
        }
        self.assertEqual(failed, {"routed_net:SCK", "routed_net:MOSI", "routed_net:MISO", "routed_net:IRQ"})
        self.assertEqual(result["details"]["dimensions"]["width_mm"], 30.0)
        self.assertEqual(result["details"]["dimensions"]["height_mm"], 25.0)

    def test_kicad_checks_treat_warnings_as_violations(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            artifacts = run_dir / "artifacts"
            artifacts.mkdir()
            (artifacts / "test.kicad_sch").write_text("(kicad_sch)\n", encoding="utf-8")
            (artifacts / "test.kicad_pcb").write_text("(kicad_pcb)\n", encoding="utf-8")
            calls = []

            def fake_run(command, cwd, timeout):
                calls.append(command)
                return {"returncode": 0, "output": "", "timed_out": False}

            with mock.patch("deepee.checks.kicad.command_available", return_value=True), mock.patch(
                "deepee.checks.kicad.run_subprocess", side_effect=fake_run
            ):
                run_kicad_erc({"name": "erc", "root": "artifacts"}, SimpleNamespace(id="task"), run_dir, {})
                run_kicad_drc({"name": "drc", "root": "artifacts"}, SimpleNamespace(id="task"), run_dir, {})
            self.assertTrue(all("--exit-code-violations" in command for command in calls))
            self.assertTrue(all("--severity-warning" in command for command in calls))
            self.assertIn("--refill-zones", calls[1])

    def test_netlist_contract_uses_exported_pin_connectivity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            artifacts = run_dir / "artifacts"
            artifacts.mkdir()
            (artifacts / "design.kicad_sch").write_text("(kicad_sch)\n", encoding="utf-8")

            def fake_run(command, cwd, timeout):
                output = Path(command[command.index("--output") + 1])
                output.write_text(
                    """<export><components><comp ref=\"U1\"><value>Sensor</value><footprint>Pkg</footprint></comp></components><nets><net code=\"1\" name=\"SDA\"><node ref=\"U1\" pin=\"1\"/></net></nets></export>""",
                    encoding="utf-8",
                )
                return {"returncode": 0, "output": "", "timed_out": False}

            check = {
                "schematic": "artifacts/design.kicad_sch",
                "exact_references": True,
                "components": [{"reference": "U1", "value": "Sensor", "footprint": "Pkg"}],
                "pin_nets": {"U1.1": "SDA"},
            }
            with mock.patch("deepee.checks.kicad_netlist.command_available", return_value=True), mock.patch(
                "deepee.checks.kicad_netlist.run_subprocess", side_effect=fake_run
            ):
                payload = run_kicad_netlist_contract(check, SimpleNamespace(id="task"), run_dir, {})
            self.assertTrue(payload["passed"], payload)

    def test_netlist_contract_normalizes_root_sheet_local_label(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            artifacts = run_dir / "artifacts"
            artifacts.mkdir()
            (artifacts / "design.kicad_sch").write_text("(kicad_sch)\n", encoding="utf-8")

            def fake_run(command, cwd, timeout):
                output = Path(command[command.index("--output") + 1])
                output.write_text(
                    """<export><components><comp ref=\"U1\"><value>Sensor</value><footprint>Pkg</footprint></comp></components><nets><net code=\"1\" name=\"/SDA\"><node ref=\"U1\" pin=\"1\"/></net></nets></export>""",
                    encoding="utf-8",
                )
                return {"returncode": 0, "output": "", "timed_out": False}

            check = {
                "schematic": "artifacts/design.kicad_sch",
                "components": [{"reference": "U1", "value": "Sensor", "footprint": "Pkg"}],
                "pin_nets": {"U1.1": "SDA"},
            }
            with mock.patch("deepee.checks.kicad_netlist.command_available", return_value=True), mock.patch(
                "deepee.checks.kicad_netlist.run_subprocess", side_effect=fake_run
            ):
                payload = run_kicad_netlist_contract(check, SimpleNamespace(id="task"), run_dir, {})
            self.assertTrue(payload["passed"], payload)
            self.assertIn("SDA", payload["details"]["nets"])

    def test_hardware_tasks_fix_components_but_not_golden_geometry(self) -> None:
        for task in iter_tasks(REPO_ROOT):
            if task.suite not in {"schematic", "schematic-design", "pcb", "pcb-design"}:
                continue
            structure_type = "kicad_schematic_structure" if "schematic" in task.suite else "kicad_pcb_structure"
            structure = next(check for check in task.manifest["checks"] if check["type"] == structure_type)
            self.assertTrue(structure.get("exact_references"), task.id)
            self.assertTrue(structure.get("components"), task.id)
            prompt = task.prompt_path.read_text(encoding="utf-8").lower()
            self.assertNotIn("benchmark", prompt)
            self.assertNotIn("verifier", prompt)
            self.assertTrue((task.path / "SOURCE.md").is_file(), task.id)

    def test_mcp9808_tasks_require_alert_pullup(self) -> None:
        for task_id in ("deepee-sch-002", "deepee-pcb-002"):
            task = resolve_task(task_id, REPO_ROOT)
            structure = next(check for check in task.manifest["checks"] if check["type"].endswith("_structure"))
            r3 = next(component for component in structure["components"] if component["reference"] == "R3")
            self.assertEqual(r3["value"], "10k")
            connectivity = structure if "pin_nets" in structure else next(
                check for check in task.manifest["checks"] if check["type"] == "kicad_netlist_contract"
            )
            self.assertEqual(connectivity["pin_nets"]["R3.1"], "3V3")
            self.assertEqual(connectivity["pin_nets"]["R3.2"], "ALERT")

    @unittest.skipUnless(shutil.which("cc"), "C compiler required")
    def test_reference_solutions_cover_all_tasks_and_pass_host_checks(self) -> None:
        tasks = list(iter_tasks(REPO_ROOT))
        self.assertEqual(
            {task.id for task in tasks},
            {path.name for path in SOLUTIONS.iterdir() if path.is_dir()},
        )
        with tempfile.TemporaryDirectory() as tmp:
            for task in tasks:
                run_dir = assemble_reference_run(task, Path(tmp) / task.id)
                payload = verify_task(task.id, run_dir, allow_missing_tools=True, root=REPO_ROOT)
                for check in payload["checks"]:
                    if check.get("skipped"):
                        self.assertIn(check["type"], {"firmware_build", "kicad_erc", "kicad_drc", "kicad_netlist_contract"})
                    else:
                        self.assertTrue(check["passed"], (task.id, check))

    def test_public_docs_make_no_tool_neutral_claim(self) -> None:
        text = "\n".join(
            path.read_text(encoding="utf-8")
            for root in (REPO_ROOT / "docs", REPO_ROOT / "agents")
            for path in root.glob("*.md")
        ) + (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        self.assertNotIn("neutral-exchange", text)
        self.assertNotIn("verification_track", text)
        self.assertIn("not a tool-agnostic", text)

    def test_agent_proxy_allows_only_the_openai_https_authority(self) -> None:
        path = REPO_ROOT / "docker" / "api_egress_proxy.py"
        spec = importlib.util.spec_from_file_location("deepee_api_egress_proxy", path)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertEqual(module.ALLOWED_HOSTS, frozenset({"api.openai.com"}))
        with mock.patch.dict(os.environ, {"DEEPEE_CHATGPT_AUTH": "0"}):
            self.assertEqual(module._allowed_hosts(), frozenset({"api.openai.com"}))
        self.assertEqual(module._parse_authority("api.openai.com:443"), ("api.openai.com", 443))
        for invalid in ("api.openai.com:80", "api.openai.com.evil:443", "user@api.openai.com:443"):
            if invalid.endswith(".evil:443"):
                host, port = module._parse_authority(invalid)
                self.assertNotIn(host, module.ALLOWED_HOSTS)
                self.assertEqual(port, 443)
            else:
                with self.assertRaises(ValueError):
                    module._parse_authority(invalid)

    def test_agent_proxy_chatgpt_profile_remains_openai_only(self) -> None:
        path = REPO_ROOT / "docker" / "api_egress_proxy.py"
        spec = importlib.util.spec_from_file_location("deepee_api_egress_proxy_chatgpt", path)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with mock.patch.dict(os.environ, {"DEEPEE_CHATGPT_AUTH": "1"}):
            self.assertEqual(
                module._allowed_hosts(),
                frozenset({"api.openai.com", "auth.openai.com", "chatgpt.com"}),
            )


if __name__ == "__main__":
    unittest.main()
