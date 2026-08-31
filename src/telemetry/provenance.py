"""Dataset provenance tracking, checksum verification, and attribution logger."""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class DatasetMetadata(BaseModel):
    """Immutable record of dataset origin, licensing, and file checksums."""
    dataset_name: str
    source_url: str
    access_date_utc: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    license_or_terms: str
    citation: str
    description: str
    file_hashes_sha256: Dict[str, str] = Field(default_factory=dict)
    notes: Optional[str] = None


class DatasetProvenanceTracker:
    """Manages recording and verification of dataset provenance metadata."""

    def __init__(self, metadata_dir: str = "data"):
        self.metadata_dir = Path(metadata_dir)
        self.metadata_dir.mkdir(parents=True, exist_ok=True)
        self.provenance_file = self.metadata_dir / "provenance.json"

    @staticmethod
    def compute_sha256(file_path: str | Path) -> str:
        """Compute SHA-256 hash of a file for immutability validation."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(65536), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def record_provenance(self, meta: DatasetMetadata) -> None:
        """Save or update dataset provenance records."""
        records: Dict[str, Any] = {}
        if self.provenance_file.exists():
            try:
                with open(self.provenance_file, "r", encoding="utf-8") as f:
                    records = json.load(f)
            except Exception:
                records = {}

        records[meta.dataset_name] = meta.model_dump()
        with open(self.provenance_file, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2)

    def get_provenance(self, dataset_name: str) -> Optional[DatasetMetadata]:
        """Retrieve recorded provenance for a dataset."""
        if not self.provenance_file.exists():
            return None
        with open(self.provenance_file, "r", encoding="utf-8") as f:
            records = json.load(f)
        data = records.get(dataset_name)
        if data:
            return DatasetMetadata(**data)
        return None

    def verify_integrity(self, dataset_name: str, base_dir: str | Path) -> Dict[str, bool]:
        """Verify that files match their recorded SHA256 checksums."""
        meta = self.get_provenance(dataset_name)
        if not meta:
            raise ValueError(f"No provenance record found for '{dataset_name}'")

        results = {}
        base_path = Path(base_dir)
        for rel_path, expected_hash in meta.file_hashes_sha256.items():
            full_path = base_path / rel_path
            if not full_path.exists():
                results[rel_path] = False
                continue
            actual_hash = self.compute_sha256(full_path)
            results[rel_path] = (actual_hash == expected_hash)
        return results
