from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
from typing import Iterable, Mapping, Sequence

CHUNK_SIZE = 1024 * 1024


class RunLedgerError(RuntimeError):
    pass


@dataclass(frozen=True)
class FileDigest:
    path: str
    sha256: str


@dataclass(frozen=True)
class Receipt:
    version: int
    command: tuple[str, ...]
    cwd: str
    git_head: str | None
    environment: Mapping[str, str]
    inputs: tuple[FileDigest, ...]
    outputs: tuple[FileDigest, ...]
    started_at: str
    finished_at: str
    duration_ms: float
    exit_code: int

    def as_dict(self) -> dict:
        return {
            "version": self.version,
            "command": list(self.command),
            "cwd": self.cwd,
            "git": {"head": self.git_head},
            "environment": dict(sorted(self.environment.items())),
            "inputs": [x.__dict__ for x in self.inputs],
            "outputs": [x.__dict__ for x in self.outputs],
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "duration_ms": self.duration_ms,
            "exit_code": self.exit_code,
        }


def _git_head(cwd: Path) -> str | None:
    try:
        p = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=cwd, check=True,
            capture_output=True, text=True, stdin=subprocess.DEVNULL,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    return p.stdout.strip() or None


def _resolve_inside(root: Path, raw: str) -> tuple[str, Path]:
    base = root.resolve()
    path = (base / raw).resolve()
    try:
        rel = path.relative_to(base).as_posix()
    except ValueError as exc:
        raise RunLedgerError(f"path escapes cwd: {raw}") from exc
    return rel, path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(CHUNK_SIZE):
            digest.update(chunk)
    return digest.hexdigest()


def _digests(root: Path, paths: Iterable[str]) -> tuple[FileDigest, ...]:
    result: list[FileDigest] = []
    for raw in paths:
        rel, path = _resolve_inside(root, raw)
        if not path.is_file():
            raise RunLedgerError(f"declared file is missing or not regular: {raw}")
        result.append(FileDigest(rel, sha256_file(path)))
    return tuple(sorted(result, key=lambda item: item.path))


def record(command: Sequence[str], *, cwd: Path, env_names: Iterable[str] = (),
           input_paths: Iterable[str] = (), output_paths: Iterable[str] = ()) -> tuple[Receipt, int]:
    if not command:
        raise RunLedgerError("a command is required")
    root = cwd.resolve()
    if not root.is_dir():
        raise RunLedgerError(f"cwd is not a directory: {cwd}")

    env_names = tuple(env_names)
    for name in env_names:
        if not name or "=" in name:
            raise RunLedgerError(f"invalid environment variable name: {name!r}")

    started = datetime.now(timezone.utc)
    inputs = _digests(root, input_paths)
    child_env = os.environ.copy()
    selected_env = {name: child_env[name] for name in env_names if name in child_env}

    completed = subprocess.run(
        list(command), cwd=root, env=child_env,
        stdin=subprocess.DEVNULL, stdout=None, stderr=None,
        shell=False, check=False,
    )

    outputs = _digests(root, output_paths)
    finished = datetime.now(timezone.utc)
    receipt = Receipt(
        version=1, command=tuple(command), cwd=str(root),
        git_head=_git_head(root), environment=selected_env,
        inputs=inputs, outputs=outputs, started_at=started.isoformat(),
        finished_at=finished.isoformat(),
        duration_ms=round((finished - started).total_seconds() * 1000.0, 3),
        exit_code=completed.returncode,
    )
    return receipt, completed.returncode


def write_receipt(path: Path, receipt: Receipt) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(receipt.as_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
