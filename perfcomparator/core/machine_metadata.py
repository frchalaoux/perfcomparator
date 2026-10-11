"""Métadonnées de machine corrigées par l’utilisateur."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field, field_validator


class MachineMetadataOverride(BaseModel):
    model: str = Field(min_length=1, max_length=200)
    model_year: int | None = Field(default=None, ge=1984, le=2100)
    product_sku: str | None = Field(default=None, max_length=100)

    @field_validator("model")
    @classmethod
    def normalize_model(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Le modèle ne peut pas être vide.")
        return normalized

    @field_validator("product_sku")
    @classmethod
    def normalize_product_sku(cls, value: str | None) -> str | None:
        normalized = " ".join(value.split()) if value else ""
        return normalized or None


class MachineMetadataStore:
    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)

    def load(self) -> MachineMetadataOverride | None:
        if not self.path.exists():
            return None
        return MachineMetadataOverride.model_validate_json(
            self.path.read_text(encoding="utf-8")
        )

    def save(self, metadata: MachineMetadataOverride) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_name(f"{self.path.name}.tmp")
        try:
            temporary.write_text(metadata.model_dump_json(indent=2), encoding="utf-8")
            temporary.replace(self.path)
        finally:
            temporary.unlink(missing_ok=True)
