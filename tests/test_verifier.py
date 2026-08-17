from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from deepee.benchmark import run_benchmark_suite
from deepee.container import verify_task_in_container
from deepee.doctor import run_doctor
from deepee.lint import lint_tasks
from deepee.report import collect_results
from deepee.runner import prepare_run
from deepee.verifier import verify_task


REPO_ROOT = Path(__file__).resolve().parents[1]


def _make_artifact_task(root: Path, task_id: str = "sample-fw") -> Path:
    task_dir = root / "tasks" / "firmware" / task_id
    (task_dir / "starter").mkdir(parents=True)
    (task_dir / "prompt.md").write_text("Create artifacts/result.txt.\n", encoding="utf-8")
    (task_dir / "expected_artifacts.yaml").write_text("required:\n  - artifacts/result.txt\n", encoding="utf-8")
    (task_dir / "manifest.yaml").write_text(
        f"""id: {task_id}
suite: firmware
contract_version: '2.0'
required_artifacts:
  - {{path: artifacts/result.txt, kind: file}}
requirements:
  - id: result-exists
    description: Produce the required result artifact.
    layer: deliverable
    critical: true
    check: result_exists
checks:
  - type: artifact_presence
    name: result_exists
""",
        encoding="utf-8",
    )
    return task_dir


def _manual_agent(root: Path) -> Path:
    agent = root / "agent.yaml"
    agent.write_text("id: manual-agent\nrunner:\n  type: manual\n  command: null\n", encoding="utf-8")
    return agent


def _score(
    created_at: str,
    passed: bool,
    publishable: bool,
    run_id: str,
    *,
    task_id: str = "sample-fw",
    benchmark_hash: str = "bench",
    required_tasks: tuple[str, ...] = ("sample-fw",),
) -> dict:
    return {
        "schema_version": "1.0",
        "task_id": task_id,
        "suite": "firmware",
        "agent": {"id": "agent-a"},
        "run_dir": "/tmp/run",
        "score": 1.0 if passed else 0.0,
        "passed": passed,
        "publishable": publishable,
        "failures": [] if passed else ["check"],
        "checks": [],
        "metadata": {
            "hashes": {"task": "task", "benchmark": benchmark_hash, "submission": "submission", "artifacts": "artifacts"},
            "benchmark_task_ids": list(required_tasks),
            "run": {
                "created_at": created_at,
                "run_id": run_id,
                "usage": {},
                "cost_estimate": {"total_usd": 1.25},
                "network_policy": {
                    "profile": "api_key",
                    "effective_profile": "api_key",
                    "authentication": "api_key",
                    "agent_egress": ["api.openai.com:443"],
                    "verifier_egress": [],
                },
                "agent_config_hash": "config-a",
            },
        },
    }


class VerifierTests(unittest.TestCase):
    def test_verifier_is_strictly_binary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _make_artifact_task(root)
            run_dir = root / "run"
            (run_dir / "artifacts").mkdir(parents=True)
            (run_dir / "artifacts" / "result.txt").write_text("ok\n", encoding="utf-8")
            (run_dir / ".deepee").mkdir()
            (run_dir / ".deepee" / "run.json").write_text(
                json.dumps(
                    {
                        "cost_estimate": {"total_usd": 1.25},
                        "network_policy": {
                            "profile": "api_key",
                            "effective_profile": "api_key",
                            "authentication": "api_key",
                            "agent_egress": ["api.openai.com:443"],
                            "verifier_egress": [],
                        },
                    }
                ),
                encoding="utf-8",
            )
            passed = verify_task("sample-fw", run_dir, root=root)
            self.assertTrue(passed["passed"])
            self.assertEqual(passed["score"], 1.0)
            self.assertEqual(passed["schema_version"], "2.0")
            self.assertEqual(passed["critical_requirement_failures"], [])
            self.assertEqual(passed["requirements"][0]["id"], "result-exists")
            self.assertEqual(passed["score_vector"]["deliverable"]["pass_rate"], 1.0)
            self.assertEqual(len(passed["metadata"]["hashes"]["decision"]), 64)
            self.assertEqual(passed["metadata"]["run"]["cost_estimate"]["total_usd"], 1.25)
            self.assertEqual(passed["metadata"]["run"]["network_policy"]["effective_profile"], "api_key")
            repeated = verify_task("sample-fw", run_dir, root=root)
            self.assertEqual(
                passed["metadata"]["hashes"]["decision"],
                repeated["metadata"]["hashes"]["decision"],
            )

            (run_dir / "artifacts" / "result.txt").unlink()
            failed = verify_task("sample-fw", run_dir, root=root)
            self.assertFalse(failed["passed"])
            self.assertEqual(failed["score"], 0.0)
            self.assertEqual(failed["failures"], ["result_exists"])
            self.assertEqual(failed["critical_requirement_failures"], ["result-exists"])

    def test_incomplete_automated_agent_run_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _make_artifact_task(root)
            run_dir = root / "run"
            (run_dir / "artifacts").mkdir(parents=True)
            (run_dir / "artifacts" / "result.txt").write_text("ok\n", encoding="utf-8")
            (run_dir / ".deepee").mkdir()
            (run_dir / ".deepee" / "run.json").write_text(
                json.dumps({"agent": {"runner": {"command": ["agent"]}}, "status": "failed"}),
                encoding="utf-8",
            )
            payload = verify_task("sample-fw", run_dir, root=root)
            self.assertFalse(payload["passed"])
            self.assertIn("agent_run_completed", payload["failures"])

    def test_lint_rejects_removed_scoring_fields_and_unknown_checks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            task_dir = _make_artifact_task(root)
            (task_dir / "manifest.yaml").write_text(
                """id: sample-fw
suite: firmware
contract_version: '2.0'
pass_threshold: 0.8
required_artifacts:
  - {path: artifacts/result.txt, kind: file}
requirements:
  - id: invalid-check
    description: Exercise lint rejection.
    layer: deliverable
    critical: true
    check: definitely_not_a_check
checks:
  - type: definitely_not_a_check
    weight: 1
""",
                encoding="utf-8",
            )
            payload = lint_tasks(root)
            messages = [error["message"] for error in payload["errors"]]
            self.assertFalse(payload["ok"])
            self.assertTrue(any("removed key: pass_threshold" in message for message in messages))
            self.assertTrue(any("removed key: weight" in message for message in messages))
            self.assertTrue(any("unknown check type" in message for message in messages))

    def test_repository_lint_passes(self) -> None:
        payload = lint_tasks(REPO_ROOT)
        self.assertTrue(payload["ok"], payload)
        self.assertEqual(payload["task_count"], 48)

    def test_prepare_run_uses_unique_run_ids(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _make_artifact_task(root)
            agent = _manual_agent(root)
            first = prepare_run(agent, "sample-fw", root / "runs", root)
            second = prepare_run(agent, "sample-fw", root / "runs", root)
            self.assertNotEqual(first["run_dir"], second["run_dir"])
            self.assertNotEqual(first["run_id"], second["run_id"])
            self.assertTrue((Path(second["run_dir"]) / "artifacts").is_dir())

    def test_manual_benchmark_prepare_only_does_not_verify(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _make_artifact_task(root)
            agent = _manual_agent(root)
            payload = run_benchmark_suite(
                [agent],
                task_refs=["sample-fw"],
                runs_root=root / "runs",
                results_dir=root / "results" / "scored",
                prepare_only=True,
                update_report=False,
                root=root,
            )
            self.assertTrue(payload["ok"])
            self.assertEqual(payload["runs"][0]["status"], "prepared")
            self.assertFalse(payload["runs"][0]["verified"])

    def test_doctor_reports_manual_agent_ready_without_hardware_tools(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, mock.patch(
            "deepee.doctor._command_version", return_value={"available": True, "version": "test"}
        ):
            root = Path(tmp)
            _make_artifact_task(root)
            agent = _manual_agent(root)
            payload = run_doctor([agent], root=root)
            self.assertTrue(payload["ok"], payload)
            self.assertEqual(payload["agents"][0]["mode"], "manual")

    def test_container_verification_mounts_submission_read_only(self) -> None:
        commands = []

        def fake_run(command, **kwargs):
            commands.append(command)
            if command[1:3] == ["image", "inspect"]:
                return subprocess.CompletedProcess(command, 0, "sha256:verifier\n")
            if command[1:] == ["--version"]:
                return subprocess.CompletedProcess(command, 0, "Docker test\n")
            verification_mount = next(
                item for item in command if item.startswith("type=bind,src=") and item.endswith(",dst=/verification")
            )
            verification_root = Path(verification_mount.removeprefix("type=bind,src=").removesuffix(",dst=/verification"))
            (verification_root / "work").mkdir(exist_ok=True)
            (verification_root / "score.json").write_text(
                json.dumps({"task_id": "sample-fw", "passed": False, "score": 0.0, "metadata": {}}),
                encoding="utf-8",
            )
            return subprocess.CompletedProcess(command, 1, "failed score\n")

        with tempfile.TemporaryDirectory() as tmp, mock.patch(
            "deepee.container.shutil.which", return_value="/usr/bin/docker"
        ), mock.patch("deepee.container.subprocess.run", side_effect=fake_run):
            run_dir = Path(tmp) / "run"
            run_dir.mkdir()
            payload = verify_task_in_container("sample-fw", run_dir, "verifier:test")

        docker_run = next(command for command in commands if len(command) > 1 and command[1] == "run")
        self.assertIn(f"type=bind,src={run_dir.resolve()},dst=/submission,readonly", docker_run)
        self.assertTrue(any(item.endswith(",dst=/verification") for item in docker_run))
        user_index = docker_run.index("--user")
        self.assertEqual(docker_run[user_index + 1], "benchmark")
        self.assertTrue(any("chmod a+rwX" in item for item in docker_run))
        self.assertTrue(payload["metadata"]["verification_container"]["submission_read_only"])
        self.assertFalse(payload["passed"])

    def test_report_counts_only_first_publishable_attempt(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            results = root / "scored"
            results.mkdir()
            (results / "01.json").write_text(json.dumps(_score("2026-01-01T00:00:00Z", False, True, "run-1")), encoding="utf-8")
            (results / "02.json").write_text(json.dumps(_score("2026-01-01T00:01:00Z", True, True, "run-2")), encoding="utf-8")
            (results / "03.json").write_text(json.dumps(_score("2025-12-31T23:59:00Z", True, False, "dry-run")), encoding="utf-8")
            report = collect_results(results, root / "report.json")
            self.assertEqual(report["total_runs"], 3)
            self.assertEqual(report["total_publishable_runs"], 2)
            self.assertEqual(report["total_first_attempts"], 1)
            self.assertEqual(report["total_estimated_api_cost_usd"], 3.75)
            cohort = next(iter(report["by_agent"].values()))
            self.assertEqual(cohort["pass_at_1"], 0.0)
            self.assertEqual(cohort["estimated_api_cost_usd"], 1.25)
            self.assertEqual(cohort["network_policy"]["effective_profile"], "api_key")
            self.assertTrue(cohort["complete"])
            publishable = [row for row in report["runs"] if row["publishable"]]
            self.assertTrue(publishable[0]["counts_for_pass_at_1"])
            self.assertFalse(publishable[1]["counts_for_pass_at_1"])

    def test_report_never_scores_an_incomplete_cohort(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            results = root / "scored"
            results.mkdir()
            score = _score(
                "2026-01-01T00:00:00Z",
                True,
                True,
                "run-1",
                required_tasks=("sample-fw", "sample-pcb"),
            )
            (results / "01.json").write_text(json.dumps(score), encoding="utf-8")
            report = collect_results(results, root / "report.json")
            cohort = next(iter(report["by_agent"].values()))
            self.assertFalse(cohort["complete"])
            self.assertIsNone(cohort["pass_at_1"])
            self.assertEqual(cohort["missing_task_ids"], ["sample-pcb"])

    def test_report_separates_benchmark_hashes_into_distinct_attempts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            results = root / "scored"
            results.mkdir()
            first = _score("2026-01-01T00:00:00Z", False, True, "run-1", benchmark_hash="bench-a")
            second = _score("2026-01-01T00:01:00Z", True, True, "run-2", benchmark_hash="bench-b")
            (results / "01.json").write_text(json.dumps(first), encoding="utf-8")
            (results / "02.json").write_text(json.dumps(second), encoding="utf-8")
            report = collect_results(results, root / "report.json")
            self.assertEqual(len(report["by_agent"]), 2)
            self.assertEqual([row["attempt_index"] for row in report["runs"]], [1, 1])
            self.assertTrue(all(row["counts_for_pass_at_1"] for row in report["runs"]))


if __name__ == "__main__":
    unittest.main()
