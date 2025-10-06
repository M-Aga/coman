#!/usr/bin/env python3
"""Capture run_coman output into a timestamped log file.

This helper runs a command (``./run_coman.sh`` by default) and mirrors its
stdout/stderr to both the console and a structured log file.  It is useful when
sharing diagnostics or reproductions because it keeps the raw output alongside a
small metadata header that records the invocation details.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import os
import pathlib
import subprocess
import sys
from typing import Iterable, Sequence


def _default_log_dir() -> pathlib.Path:
    env_value = os.environ.get("COMAN_LOG_DIR")
    if env_value:
        return pathlib.Path(env_value).expanduser().resolve()
    return pathlib.Path("logs").resolve()


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Capture command output to a log file")
    parser.add_argument(
        "--command",
        nargs=argparse.REMAINDER,
        help="Command to execute (defaults to ./run_coman.sh if omitted)",
    )
    parser.add_argument(
        "--log-dir",
        type=pathlib.Path,
        default=None,
        help="Directory where log files should be written (defaults to ./logs or $COMAN_LOG_DIR)",
    )
    parser.add_argument(
        "--no-stdout",
        action="store_true",
        help="Do not mirror the captured output to the current stdout",
    )
    return parser


def _resolve_command(args: argparse.Namespace) -> Sequence[str]:
    if args.command:
        return args.command
    return ("./run_coman.sh",)


def _prepare_log_file(log_dir: pathlib.Path, command: Sequence[str]) -> pathlib.Path:
    timestamp = _dt.datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    sanitized = "_".join(part.replace(os.sep, "-") for part in command if part)
    if not sanitized:
        sanitized = "command"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / f"coman-log-{timestamp}-{sanitized}.log"


def _write_header(file_obj, command: Sequence[str]) -> None:
    file_obj.write("# coman log capture\n")
    file_obj.write(f"# timestamp_utc: {_dt.datetime.utcnow().isoformat()}Z\n")
    file_obj.write(f"# cwd: {os.getcwd()}\n")
    file_obj.write(f"# command: {' '.join(command)}\n")
    file_obj.write("# --- begin output ---\n")
    file_obj.flush()


def _stream_output(proc: subprocess.Popen[str], targets: Iterable) -> None:
    assert proc.stdout is not None
    for line in proc.stdout:
        for target in targets:
            target.write(line)
            target.flush()


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()
    command = _resolve_command(args)
    log_dir = args.log_dir.resolve() if args.log_dir else _default_log_dir()
    log_file_path = _prepare_log_file(log_dir, command)

    try:
        with open(log_file_path, "w", encoding="utf-8") as log_file:
            _write_header(log_file, command)
            display_targets = [log_file]
            if not args.no_stdout:
                display_targets.append(sys.stdout)

            with subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            ) as proc:
                try:
                    _stream_output(proc, display_targets)
                except KeyboardInterrupt:
                    proc.terminate()
                    proc.wait()
                returncode = proc.poll()

            log_file.write(f"\n# --- process exited with code {returncode} ---\n")
            log_file.flush()
    except FileNotFoundError as exc:
        parser.error(str(exc))
        return 2

    if not args.no_stdout:
        print(f"\nlog saved to: {log_file_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
