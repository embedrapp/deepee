from __future__ import annotations

import argparse
from pathlib import Path

from .archive import package_run
from .benchmark import run_benchmark_suite
from .container import verify_task_in_container
from .doctor import run_doctor
from .lint import lint_tasks
from .report import collect_results
from .runner import prepare_run, run_agent
from .task import iter_tasks
from .verifier import verify_task


def main() -> None:
    parser = argparse.ArgumentParser(prog="deepee")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list-tasks")
    subparsers.add_parser("lint")

    doctor = subparsers.add_parser("doctor")
    doctor.add_argument("--agent", action="append", default=[])
    doctor.add_argument("--strict-tools", action="store_true")

    prepare = subparsers.add_parser("prepare-run")
    prepare.add_argument("--agent", required=True)
    prepare.add_argument("--task", required=True)
    prepare.add_argument("--runs-root")

    run = subparsers.add_parser("run-agent")
    run.add_argument("--agent", required=True)
    run.add_argument("--task", required=True)
    run.add_argument("--runs-root")

    verify = subparsers.add_parser("verify")
    verify.add_argument("--task", required=True)
    verify.add_argument("--run-dir", required=True)
    verify.add_argument("--output")
    verify.add_argument("--allow-missing-tools", action="store_true")
    verify.add_argument("--container-image")

    report = subparsers.add_parser("report")
    report.add_argument("--results-dir")
    report.add_argument("--output")

    package = subparsers.add_parser("package-run")
    package.add_argument("--run-dir", required=True)
    package.add_argument("--output", required=True)

    benchmark = subparsers.add_parser("benchmark")
    benchmark.add_argument("--agent", action="append", required=True)
    benchmark.add_argument("--task", action="append")
    benchmark.add_argument("--all-tasks", action="store_true")
    benchmark.add_argument("--runs-root")
    benchmark.add_argument("--results-dir")
    benchmark.add_argument("--allow-missing-tools", action="store_true")
    benchmark.add_argument("--prepare-only", action="store_true")
    benchmark.add_argument("--no-report", action="store_true")
    benchmark.add_argument("--verification-image")

    args = parser.parse_args()
    if args.command == "list-tasks":
        for task in iter_tasks():
            difficulty = task.manifest.get("difficulty", "unknown")
            print(f"{task.id}\t{task.suite}\t{difficulty}\t{task.path}")
        return

    if args.command == "lint":
        payload = lint_tasks()
        if payload["ok"]:
            print(f"Lint passed for {payload['task_count']} task(s)")
            return
        for error in payload["errors"]:
            print(f"{error['task_id']}: {error['message']} ({error['path']})")
        raise SystemExit(1)

    if args.command == "doctor":
        payload = run_doctor(
            [Path(agent) for agent in args.agent],
            strict_tools=args.strict_tools,
        )
        print(f"Tasks: {payload['task_count']}")
        print(f"Lint: {'ok' if payload['lint']['ok'] else 'failed'}")
        for name, status in payload["tools"].items():
            marker = "ok" if status["available"] else "missing"
            version = f" - {status.get('version')}" if status.get("version") else ""
            print(f"Tool {name}: {marker}{version}")
        for agent in payload["agents"]:
            marker = "ok" if agent["available"] else "missing"
            print(f"Agent {agent['agent_id']}: {marker} ({agent['mode']})")
        if payload["ok"]:
            print("Doctor passed")
            return
        if payload["missing_core_tools"]:
            print(f"Missing core tools: {', '.join(payload['missing_core_tools'])}")
        if payload["missing_agents"]:
            print(f"Missing agent commands: {', '.join(payload['missing_agents'])}")
        if args.strict_tools and payload["missing_optional_tools"]:
            print(f"Missing optional tools: {', '.join(payload['missing_optional_tools'])}")
        raise SystemExit(1)

    if args.command == "prepare-run":
        metadata = prepare_run(
            Path(args.agent),
            args.task,
            Path(args.runs_root) if args.runs_root else None,
        )
        print(metadata["run_dir"])
        return

    if args.command == "run-agent":
        metadata = run_agent(
            Path(args.agent),
            args.task,
            Path(args.runs_root) if args.runs_root else None,
        )
        print(metadata["run_dir"])
        return

    if args.command == "verify":
        if args.container_image:
            payload = verify_task_in_container(
                args.task,
                Path(args.run_dir),
                image=args.container_image,
                output=Path(args.output) if args.output else None,
                allow_missing_tools=args.allow_missing_tools,
            )
        else:
            payload = verify_task(
                args.task,
                Path(args.run_dir),
                Path(args.output) if args.output else None,
                allow_missing_tools=args.allow_missing_tools,
            )
        print(f"{payload['task_id']}: score={payload['score']:.3f} passed={payload['passed']}")
        if not payload["passed"]:
            raise SystemExit(1)
        return

    if args.command == "report":
        payload = collect_results(
            Path(args.results_dir) if args.results_dir else None,
            Path(args.output) if args.output else None,
        )
        print(f"Collected {payload['total_runs']} scored run(s)")
        return

    if args.command == "package-run":
        payload = package_run(Path(args.run_dir), Path(args.output))
        print(f"Packaged {payload['file_count']} file(s): {payload['path']} sha256={payload['sha256']}")
        return

    if args.command == "benchmark":
        payload = run_benchmark_suite(
            [Path(agent) for agent in args.agent],
            task_refs=args.task,
            all_tasks=args.all_tasks,
            runs_root=Path(args.runs_root) if args.runs_root else None,
            results_dir=Path(args.results_dir) if args.results_dir else None,
            allow_missing_tools=args.allow_missing_tools,
            prepare_only=args.prepare_only,
            update_report=not args.no_report,
            verification_image=args.verification_image,
        )
        if not payload["ok"]:
            print(f"Benchmark stopped at {payload['stage']}")
            for error in payload.get("lint", {}).get("errors", []):
                print(f"{error['task_id']}: {error['message']}")
            raise SystemExit(1)
        for run_info in payload["runs"]:
            if run_info["verified"]:
                print(
                    f"{run_info['agent_id']} {run_info['task_id']}: "
                    f"score={run_info['score']:.3f} passed={run_info['passed']} "
                    f"score_file={run_info['score_file']}"
                )
            else:
                print(
                    f"{run_info['agent_id']} {run_info['task_id']}: "
                    f"prepared run_dir={run_info['run_dir']}"
                )
        return


if __name__ == "__main__":
    main()
