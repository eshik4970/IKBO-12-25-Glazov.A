"""In-memory virtual file system backed by a CSV file."""

import base64
import csv
from dataclasses import dataclass
from pathlib import PurePosixPath


@dataclass(frozen=True)
class Entry:
    path: str
    kind: str
    content: bytes = b""


class VirtualFileSystem:
    """Read a CSV representation into memory, without modifying the source."""

    def __init__(self, csv_path=None):
        self.entries = {"/": Entry("/", "dir")}
        if csv_path is not None:
            with open(csv_path, "r", encoding="utf-8", newline="") as handle:
                self.load(handle)

    @staticmethod
    def normalize(path, cwd="/"):
        if not path:
            return cwd
        combined = (
            path if path.startswith("/")
            else cwd.rstrip("/") + "/" + path
        )
        parts = []
        for part in combined.split("/"):
            if part in ("", "."):
                continue
            if part == "..":
                if parts:
                    parts.pop()
            else:
                parts.append(part)
        return "/" + "/".join(parts)

    def load(self, handle):
        reader = csv.DictReader(handle)
        required = {"path", "type", "content_base64"}
        if (
            reader.fieldnames is None
            or not required.issubset(reader.fieldnames)
        ):
            message = "VFS CSV must have path,type,content_base64 columns"
            raise ValueError(message)
        pending = []
        seen = set()
        for row in reader:
            raw = row["path"]
            if not raw or not raw.startswith("/") or self.normalize(raw) != raw:
                raise ValueError(f"Invalid absolute VFS path: {raw!r}")
            kind = row["type"]
            if kind not in ("file", "dir"):
                raise ValueError(f"Invalid VFS entry type: {kind!r}")
            if raw in seen or raw == "/":
                raise ValueError(f"Duplicate or reserved VFS path: {raw}")
            seen.add(raw)
            encoded = row["content_base64"] or ""
            if kind == "dir" and encoded:
                raise ValueError(f"Directory cannot contain file data: {raw}")
            try:
                content = (
                    base64.b64decode(encoded, validate=True)
                    if kind == "file" else b""
                )
            except (ValueError, base64.binascii.Error) as exc:
                raise ValueError(f"Invalid base64 for {raw}") from exc
            pending.append(Entry(raw, kind, content))
        new_entries = {"/": Entry("/", "dir")}
        for entry in pending:
            new_entries[entry.path] = entry
        self._validate_parents(pending, new_entries)
        self.entries = new_entries

    @staticmethod
    def _validate_parents(pending, entries):
        """Verify parent directories exist for every VFS entry."""
        for entry in pending:
            parent = str(PurePosixPath(entry.path).parent)
            if (
                parent not in entries
                or entries[parent].kind != "dir"
            ):
                message = f"Missing parent directory for {entry.path}: {parent}"
                raise ValueError(message)

    def get(self, path, cwd="/"):
        return self.entries.get(self.normalize(path, cwd))

    def list_dir(self, path, cwd="/"):
        absolute = self.normalize(path, cwd)
        entry = self.entries.get(absolute)
        if entry is None:
            raise FileNotFoundError(absolute)
        if entry.kind == "file":
            return [PurePosixPath(absolute).name]
        return sorted(
            PurePosixPath(key).name for key in self.entries
            if key != absolute
            and str(PurePosixPath(key).parent) == absolute
        )
