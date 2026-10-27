from pathlib import Path
import hashlib
import json
from uuid import uuid4
import shutil
import tempfile

def _file_checksum(path: Path) -> str:
    with path.open("rb") as file:
        return hashlib.file_digest(file,"sha256").hexdigest()

def _read_manifest(path: Path) -> list[dict]:
    if not path.exists():
        return []

    with path.open("r", encoding="utf-8") as file:
        return [
            json.loads(line)
            for line in file
            if line.strip()
            ]

def _write_manifest(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    temporary_path = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as file:
            temporary_path = Path(file.name)

            for record in records:
                file.write(json.dumps(record, ensure_ascii=False) + "\n")

        temporary_path.replace(path)

    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def register_source(
    path: Path,
    work_id: str,
    source_url: str,
    source_format: str,
    corpus: str = "bach_wtc"
    ) -> str:

    if not path.is_file():
        raise FileNotFoundError(f"File not found: {path}")

    if path.suffix.lower() != ".krn":
        raise ValueError(f"Expected a .krn file: {path}")

    checksum = _file_checksum(path)

    manifest = _read_manifest(Path("data/manifest.jsonl"))

    existing = next((entry for entry in manifest if entry.get("checksum") == checksum), None)

    if existing is not None:
        if existing["work_id"] != work_id:
            raise ValueError("This file is already registered under a different work_id")
     

        registered_path = Path(existing["source_path"])

        if (
            not registered_path.is_file()
            or _file_checksum(registered_path) != checksum
            ):
            raise ValueError(f"Registered file is missing or has changed: {registered_path}")
        return existing["source_id"]

    destination = Path("data/raw") / corpus / path.name

    if path.resolve() != destination.resolve():
        if destination.exists():
            if not destination.is_file():
                raise ValueError(f"{destination} is not a file")
            if _file_checksum(destination) != checksum:
                raise ValueError(f"Different contents already exist at {destination}")
        else:
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path,destination)

   
    entry = {
        "source_id" : f"src-{uuid4().hex}",
        "work_id" : work_id,
        "corpus" : corpus,
        "source_format" : source_format,
        "source_path" : destination.as_posix(),
        "checksum" : checksum,
        "source_url" : source_url
        }
    manifest.append(entry)
    _write_manifest(Path("data/manifest.jsonl"), manifest)
    return entry["source_id"]


def manifest_lookup(source_id: str) -> str:
    manifest = _read_manifest(Path("data/manifest.jsonl"))

    existing = next((entry for entry in manifest if entry.get("source_id") == source_id), None)

    if existing is None:
        raise ValueError(f"There is no entry in the manifest with source_id: {source_id}")
    else:
        return(existing)


