"""Archive and validate Tahap 4A research artifacts in MinIO.

The script deliberately treats the existing local Iceberg warehouse and model
registry as the source of truth.  It only uploads missing objects, never
deletes objects in MinIO, and never overwrites an existing object.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class ArchiveEntry:
    """A local artifact directory and its MinIO destination prefix."""

    source: Path
    destination: str
    include_patterns: tuple[str, ...] = ("**/*",)


def archive_manifest(project_root: Path) -> tuple[ArchiveEntry, ...]:
    """Return the fixed, non-destructive Tahap 4A archive manifest."""

    return (
        ArchiveEntry(project_root / "iceberg" / "bronze", "warehouse/iceberg/bronze"),
        ArchiveEntry(project_root / "iceberg" / "silver", "warehouse/iceberg/silver"),
        ArchiveEntry(project_root / "iceberg" / "gold", "warehouse/iceberg/gold"),
        ArchiveEntry(
            project_root / "iceberg" / "feature_store",
            "warehouse/iceberg/feature_store",
        ),
        ArchiveEntry(project_root / "models" / "gaussian_nb_v3", "models/gaussian_nb/v3"),
        ArchiveEntry(
            project_root / "results",
            "logs/timing",
            ("*timing*.csv", "*timing*.json"),
        ),
        ArchiveEntry(
            project_root / "logs",
            "logs/pipeline",
            ("*.json", "dag_id=*/**/*.log", "scheduler/**/*.log"),
        ),
    )


def _files_for(entry: ArchiveEntry) -> list[Path]:
    files: set[Path] = set()
    for pattern in entry.include_patterns:
        files.update(path for path in entry.source.glob(pattern) if path.is_file())
    return sorted(files)


def _run(command: list[str], *, capture: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, check=True, text=True, capture_output=capture)


def _minio_container() -> str:
    result = _run(["docker", "compose", "ps", "-q", "minio"], capture=True)
    container = result.stdout.strip()
    if not container:
        raise RuntimeError("Container service 'minio' tidak ditemukan atau tidak berjalan.")
    return container


def _configure_mc(container: str) -> None:
    _run(
        [
            "docker",
            "exec",
            container,
            "sh",
            "-c",
            'mc alias set local http://127.0.0.1:9000 "$MINIO_ROOT_USER" "$MINIO_ROOT_PASSWORD" >/dev/null',
        ]
    )


def _stage_entry(entry: ArchiveEntry, staging_root: Path) -> int:
    destination = staging_root / entry.destination
    count = 0
    for source_file in _files_for(entry):
        target = destination / source_file.relative_to(entry.source)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_file, target)
        count += 1
    return count


def docker_copy_source(stage_path: Path) -> str:
    """Return Docker's explicit 'copy directory contents' source notation."""

    return f"{stage_path}{os.sep}."


def recursive_list_command(destination: str) -> list[str]:
    """Build a JSON object-listing command supported by the mc client."""

    return ["mc", "ls", "--recursive", "--json", f"local/{destination}"]


def missing_relative_paths(entry: ArchiveEntry, remote_paths: set[str]) -> list[str]:
    """Return source-relative paths absent from the remote MinIO prefix."""

    return [
        source_file.relative_to(entry.source).as_posix()
        for source_file in _files_for(entry)
        if source_file.relative_to(entry.source).as_posix() not in remote_paths
    ]


def sync_entries(entries: Iterable[ArchiveEntry]) -> tuple[int, float]:
    """Copy missing artifact objects to MinIO and return (file_count, seconds)."""

    entries = tuple(entries)
    missing = [str(entry.source) for entry in entries if not entry.source.is_dir()]
    if missing:
        raise RuntimeError("Sumber lokal tidak ditemukan: " + ", ".join(missing))

    started = time.perf_counter()
    container = _minio_container()
    _configure_mc(container)
    remote_stage = f"/tmp/tahap4a-minio-{uuid.uuid4().hex}"
    total_files = 0

    with tempfile.TemporaryDirectory(prefix="tahap4a-minio-", dir=None) as local_stage:
        stage_path = Path(local_stage)
        for entry in entries:
            total_files += _stage_entry(entry, stage_path)

        _run(["docker", "cp", docker_copy_source(stage_path), f"{container}:{remote_stage}"])
        try:
            for entry in entries:
                existing = set(_remote_files(container, entry.destination))
                missing_paths = missing_relative_paths(entry, existing)
                for relative in missing_paths:
                    target = f"local/{entry.destination}/{relative}"
                    staged_file = f"{remote_stage}/{entry.destination}/{relative}"
                    _run(
                        ["docker", "exec", container, "mc", "cp", staged_file, target],
                        capture=True,
                    )
                print(
                    f"{entry.destination}: local={len(_files_for(entry))}, "
                    f"existing={len(existing)}, uploaded={len(missing_paths)}, "
                    f"skipped={len(_files_for(entry)) - len(missing_paths)}"
                )
        finally:
            _run(["docker", "exec", container, "rm", "-rf", remote_stage])

    return total_files, time.perf_counter() - started


def _remote_files(container: str, destination: str) -> list[str]:
    result = _run(
        ["docker", "exec", container, *recursive_list_command(destination)],
        capture=True,
    )
    bucket, _, prefix = destination.partition("/")
    relative_paths: list[str] = []
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        key = json.loads(line)["key"]
        normalized = key.removeprefix(f"{prefix}/") if prefix else key
        relative_paths.append(normalized)
    return relative_paths


def _exists(container: str, object_path: str) -> bool:
    result = subprocess.run(
        ["docker", "exec", container, "mc", "stat", f"local/{object_path}"],
        text=True,
        capture_output=True,
    )
    return result.returncode == 0


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _raw_dataset_matches(project_root: Path, container: str) -> bool:
    local_candidates = list((project_root / "data").glob("[([]*[Aa][Ss][Ll][Ii]*.xlsx"))
    if not local_candidates:
        local_candidates = list((project_root / "data").glob("*req_data_rut*.xlsx"))
    if not local_candidates:
        return False

    raw_candidates = [
        "raw/(asli)req_data_rut (1).xlsx",
        "raw/(ASLI)req_data_rut (1).xlsx",
        "raw/req_data_rut (1).xlsx",
    ]
    remote = next((path for path in raw_candidates if _exists(container, path)), None)
    if remote is None:
        return False

    with tempfile.TemporaryDirectory(prefix="tahap4a-raw-") as temp_dir:
        remote_temp = "/tmp/tahap4a-raw-verify.xlsx"
        try:
            _run(["docker", "exec", container, "mc", "cp", f"local/{remote}", remote_temp])
            _run(["docker", "cp", f"{container}:{remote_temp}", str(Path(temp_dir) / "raw.xlsx")])
            return _sha256(local_candidates[0]) == _sha256(Path(temp_dir) / "raw.xlsx")
        finally:
            _run(["docker", "exec", container, "rm", "-f", remote_temp])


def validate(project_root: Path) -> dict[str, bool]:
    """Validate every required artifact prefix and raw file checksum."""

    container = _minio_container()
    _configure_mc(container)
    entries = archive_manifest(project_root)
    statuses = {bucket: _exists(container, bucket) for bucket in ("raw", "warehouse", "models", "logs")}
    result = {
        "Raw Dataset": statuses["raw"] and _raw_dataset_matches(project_root, container),
    }
    labels = {
        "warehouse/iceberg/bronze": "Bronze",
        "warehouse/iceberg/silver": "Silver",
        "warehouse/iceberg/gold": "Gold",
        "warehouse/iceberg/feature_store": "Feature Store",
        "models/gaussian_nb/v3": "Model v3",
        "logs/timing": "Timing",
        "logs/pipeline": "Pipeline Logs",
    }
    for entry in entries:
        expected = len(_files_for(entry))
        actual = len(_remote_files(container, entry.destination)) if expected else 0
        result[labels[entry.destination]] = statuses[entry.destination.split("/", 1)[0]] and actual >= expected > 0
    return result


def _print_report(statuses: dict[str, bool]) -> bool:
    print("MINIO ARTIFACT VALIDATION")
    print("=========================")
    for label, passed in statuses.items():
        print(f"{label + '':<23} {'PASS' if passed else 'FAIL'}")
    overall = all(statuses.values())
    print(f"{'Overall':<23} {'PASS' if overall else 'FAIL'}")
    return overall


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sync", action="store_true", help="upload only missing archive objects before validation")
    args = parser.parse_args()
    project_root = Path(__file__).resolve().parents[1]
    try:
        if args.sync:
            count, elapsed = sync_entries(archive_manifest(project_root))
            print(f"MinIO sync: {count} source files checked in {elapsed:.2f} seconds.")
        return 0 if _print_report(validate(project_root)) else 1
    except (OSError, RuntimeError, subprocess.CalledProcessError) as error:
        print(f"MINIO ARTIFACT VALIDATION FAILED: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
