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
from jsonschema import Draft202012Validator

from deepee.archive import package_run
from deepee.checks.kicad import run_kicad_drc, run_kicad_erc
from deepee.checks.kicad_netlist import run_kicad_netlist_contract
from deepee.checks.kicad_structural import run_kicad_pcb_structure
from deepee.report import collect_results
from deepee.runner import _estimate_api_cost, _parse_jsonl, prepare_run
from deepee.task import iter_tasks, resolve_task
from deepee.verifier import verify_task
from validation.adequacy import mutate_requirement
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
        self.assertEqual(release["version"], "1.2.0")
        self.assertEqual(release["toolchain"]["kicad"], "10.0.4")
        self.assertEqual(release["toolchain"]["platformio"], "6.1.19")
        self.assertEqual(release["score_policy"]["primary_metric"], "pass_at_1")
        self.assertEqual(release["schema_version"], "2.0")
        self.assertEqual(release["score_policy"]["task_result"], "all_critical_requirements_must_pass")
        self.assertEqual(release["score_policy"]["diagnostic_metric"], "requirement_vector")
        self.assertEqual(release["score_policy"]["validator_release_gate"], "all_critical_mutants_killed")
        self.assertEqual(
            release["network_policy"]["profiles"]["api_key"]["agent_egress"],
            ["api.openai.com:443"],
        )
        self.assertEqual(
            release["network_policy"]["profiles"]["chatgpt_subscription"]["agent_egress"],
            ["api.openai.com:443", "auth.openai.com:443", "chatgpt.com:443"],
        )
        self.assertIsNone(release["network_policy"]["profiles"]["external_uncontrolled"]["agent_egress"])
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
        self.assertIn("deepee-agent:1.2.0", metadata["command"])
        self.assertEqual(metadata["container"]["verification_image"], "deepee-verifier:1.2.0")
        self.assertFalse(metadata["container"]["mount_codex_home"])
        self.assertFalse(metadata["container"]["mount_codex_auth"])
        self.assertEqual(metadata["container"]["network"], "deepee-agent-internal")
        self.assertIn("HTTPS_PROXY=http://deepee-api-egress:3128", metadata["command"])
        self.assertIn("NO_PROXY=", metadata["command"])
        self.assertFalse(any("dst=/root/.codex," in part for part in metadata["command"]))
        self.assertEqual(metadata["inner_command"][-1], "-")
        self.assertEqual(metadata["network_policy"]["effective_profile"], "api_key")
        self.assertEqual(metadata["network_policy"]["agent_egress"], ["api.openai.com:443"])
        self.assertNotIn("verification_track", metadata)

    def test_chatgpt_runner_records_and_enforces_its_network_profile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, mock.patch.dict(
            os.environ, {"DEEPEE_CHATGPT_AUTH": "1"}
        ), mock.patch(
            "deepee.runner._container_image_id", return_value="sha256:test"
        ), mock.patch("deepee.runner._container_command_version", return_value="codex test"), mock.patch(
            "deepee.runner._command_version", return_value="test"
        ):
            metadata = prepare_run(
                REPO_ROOT / "agents" / "codex-gpt-5.6-sol-xhigh-chatgpt.yaml",
                "deepee-repair-001",
                Path(tmp) / "runs",
                REPO_ROOT,
            )
            with self.assertRaisesRegex(ValueError, "does not match"):
                prepare_run(
                    REPO_ROOT / "agents" / "codex-gpt-5.6-sol-xhigh.yaml",
                    "deepee-repair-001",
                    Path(tmp) / "mismatch",
                    REPO_ROOT,
                )
        self.assertEqual(metadata["network_policy"]["effective_profile"], "chatgpt_subscription")
        self.assertEqual(
            metadata["network_policy"]["agent_egress"],
            ["api.openai.com:443", "auth.openai.com:443", "chatgpt.com:443"],
        )

    def test_committed_leaderboard_matches_its_public_schema(self) -> None:
        schema = json.loads((REPO_ROOT / "leaderboard" / "schema.json").read_text(encoding="utf-8"))
        results = json.loads((REPO_ROOT / "leaderboard" / "results.json").read_text(encoding="utf-8"))
        Draft202012Validator(schema).validate(results)

    def test_workflow_image_tags_match_the_benchmark_release(self) -> None:
        release = yaml.safe_load((REPO_ROOT / "benchmark.yaml").read_text(encoding="utf-8"))
        expected_declaration = f'DEEPEE_VERSION: "{release["version"]}"'
        for workflow in ("ci.yml", "release-images.yml"):
            text = (REPO_ROOT / ".github" / "workflows" / workflow).read_text(encoding="utf-8")
            self.assertIn(expected_declaration, text, workflow)
            self.assertNotIn("deepee-agent:1.1.0", text, workflow)
            self.assertNotIn("deepee-verifier:1.1.0", text, workflow)

    def test_agent_network_profiles_match_the_benchmark_contract(self) -> None:
        release = yaml.safe_load((REPO_ROOT / "benchmark.yaml").read_text(encoding="utf-8"))
        profiles = release["network_policy"]["profiles"]
        for config_name in (
            "codex-gpt-5.6-sol-xhigh.yaml",
            "codex-gpt-5.6-sol-xhigh-chatgpt.yaml",
            "manual-kicad.yaml",
        ):
            agent = yaml.safe_load((REPO_ROOT / "agents" / config_name).read_text(encoding="utf-8"))
            policy = agent["network_policy"]
            declared = profiles[policy["profile"]]
            self.assertEqual(policy["authentication"], declared["authentication"], config_name)
            self.assertEqual(policy["controlled"], declared["controlled"], config_name)
            self.assertEqual(policy["agent_egress"], declared["agent_egress"], config_name)
            self.assertEqual(policy["verifier_egress"], release["network_policy"]["verifier_egress"], config_name)

    @unittest.skipUnless(shutil.which("cc"), "C compiler required")
    def test_shipped_manual_agent_result_is_reportable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            metadata = prepare_run(
                REPO_ROOT / "agents" / "manual-kicad.yaml",
                "deepee-repair-001",
                root / "runs",
                REPO_ROOT,
            )
            run_dir = Path(metadata["run_dir"])
            (run_dir / "firmware" / "src" / "scheduler.c").write_text(CORRECT_SCHEDULER, encoding="utf-8")
            results_dir = root / "results"
            results_dir.mkdir()
            score_path = results_dir / "manual.json"
            verify_task("deepee-repair-001", run_dir, output=score_path, root=REPO_ROOT)
            report = collect_results(results_dir, root / "leaderboard.json")
        policy = report["runs"][0]["network_policy"]
        self.assertEqual(policy["effective_profile"], "external_uncontrolled")
        self.assertFalse(policy["controlled"])
        self.assertIsNone(policy["agent_egress"])

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

    def test_api_equivalent_cost_separates_cached_input(self) -> None:
        estimate = _estimate_api_cost(
            {"input_tokens": 1_000_000, "cached_input_tokens": 800_000, "output_tokens": 10_000},
            {
                "model": "gpt-5.6-sol",
                "per_million_tokens": {"input": 5.0, "cached_input": 0.5, "output": 30.0},
            },
        )
        self.assertEqual(estimate["tokens"]["uncached_input"], 200_000)
        self.assertEqual(estimate["components_usd"]["uncached_input"], 1.0)
        self.assertEqual(estimate["components_usd"]["cached_input"], 0.4)
        self.assertEqual(estimate["components_usd"]["output"], 0.3)
        self.assertEqual(estimate["total_usd"], 1.7)
        self.assertIsNone(estimate["actual_subscription_charge_usd"])

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

    def test_every_check_has_a_public_v2_requirement_contract(self) -> None:
        for task in iter_tasks(REPO_ROOT):
            self.assertEqual(task.manifest.get("contract_version"), "2.0", task.id)
            requirements = task.manifest.get("requirements") or []
            check_names = {
                str(check.get("name") or check.get("type"))
                for check in task.manifest["checks"]
            }
            self.assertEqual({str(item["check"]) for item in requirements}, check_names, task.id)
            self.assertTrue(all(item.get("critical") is True for item in requirements), task.id)

    def test_usb_c_pcb_contract_rejects_thin_and_length_mismatched_routes(self) -> None:
        task = resolve_task("deepee-pcb-007", REPO_ROOT)
        check = next(item for item in task.manifest["checks"] if item["type"] == "kicad_pcb_structure")
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            good_dir = assemble_reference_run(task, base / "good")
            good = run_kicad_pcb_structure(check, task, good_dir, {})
            self.assertTrue(good["passed"], good)
            metrics = good["details"]["routing_metrics"]
            self.assertEqual(metrics["USB_DP"]["widths_mm"], [0.25])
            self.assertEqual(metrics["USB_DM"]["widths_mm"], [0.25])

            thin_dir = assemble_reference_run(task, base / "thin")
            thin_board = thin_dir / "artifacts" / "usb-c-5v-sink.kicad_pcb"
            thin_board.write_text(
                thin_board.read_text(encoding="utf-8").replace("(width 0.25)", "(width 0.10)"),
                encoding="utf-8",
            )
            thin = run_kicad_pcb_structure(check, task, thin_dir, {})
            thin_failures = {
                item["name"] for item in thin["details"]["subchecks"] if not item["passed"]
            }
            self.assertIn("track_width:all-required-nets", thin_failures)

            skew_dir = assemble_reference_run(task, base / "skew")
            skew_board = skew_dir / "artifacts" / "usb-c-5v-sink.kicad_pcb"
            text = skew_board.read_text(encoding="utf-8")
            self.assertIn("(end 117.000 105.000)", text)
            skew_board.write_text(
                text.replace("(end 117.000 105.000)", "(end 119.000 105.000)", 1),
                encoding="utf-8",
            )
            skew = run_kicad_pcb_structure(check, task, skew_dir, {})
            skew_failures = {
                item["name"] for item in skew["details"]["subchecks"] if not item["passed"]
            }
            self.assertIn("matched_length:usb2-data-pair", skew_failures)

    @unittest.skipUnless(shutil.which("cc"), "C compiler required")
    def test_adequacy_mutant_restores_and_detects_buggy_repair_code(self) -> None:
        task = resolve_task("deepee-repair-001", REPO_ROOT)
        requirement = next(item for item in task.manifest["requirements"] if item["layer"] == "behavior")
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = assemble_reference_run(task, Path(tmp) / "mutant")
            mutation = mutate_requirement(task, requirement, run_dir)
            self.assertEqual(mutation["check_type"], "c_unit_tests")
            score = verify_task(task.id, run_dir, root=REPO_ROOT)
            self.assertIn(requirement["id"], score["critical_requirement_failures"])

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

    def test_hardware_prompts_disclose_every_enforced_component_identity(self) -> None:
        for task in iter_tasks(REPO_ROOT):
            if task.suite not in {"schematic", "schematic-design", "pcb", "pcb-design"}:
                continue
            structure_type = "kicad_schematic_structure" if "schematic" in task.suite else "kicad_pcb_structure"
            structure = next(check for check in task.manifest["checks"] if check["type"] == structure_type)
            prompt = task.prompt_path.read_text(encoding="utf-8")
            for component in structure["components"]:
                fields = ["reference", "value", "footprint"]
                if "schematic" in task.suite:
                    fields.append("library")
                for field in fields:
                    value = str(component.get(field) or "")
                    if value:
                        self.assertIn(value, prompt, (task.id, field, value))

    def test_hardware_prompts_name_every_protected_starter_path(self) -> None:
        for task in iter_tasks(REPO_ROOT):
            if task.suite not in {"schematic", "schematic-design", "pcb", "pcb-design"}:
                continue
            prompt = task.prompt_path.read_text(encoding="utf-8")
            for check in task.manifest["checks"]:
                if check["type"] != "starter_integrity":
                    continue
                for protected in check.get("protected_globs", []):
                    self.assertIn(protected, prompt, (task.id, protected))

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
        self.assertNotIn("complete 12-task", text)
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
