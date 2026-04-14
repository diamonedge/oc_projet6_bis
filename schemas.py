from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


CONFIG_PATH = Path(__file__).with_name("validation_config.json")


def load_validation_config() -> dict:
    if not CONFIG_PATH.exists():
        raise RuntimeError(
            f"Fichier de validation introuvable : {CONFIG_PATH}. "
            "Exécutez d'abord le script d'entraînement pour le générer."
        )

    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


_VALIDATION_CONFIG = load_validation_config()

ALLOWED_BUILDING_TYPES = set(_VALIDATION_CONFIG["allowed_building_types"])
ALLOWED_PROPERTY_TYPES = set(_VALIDATION_CONFIG["allowed_property_types"])
DECADE_MIN = int(_VALIDATION_CONFIG["decade_min"])
DECADE_MAX = int(_VALIDATION_CONFIG["decade_max"])
SURFACE_MIN = float(_VALIDATION_CONFIG["surface_min"])
SURFACE_MAX = float(_VALIDATION_CONFIG["surface_max"])


class PredictionInput(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    BuildingType: str = Field(
        min_length=1,
        max_length=100,
        description="Type de bâtiment exactement conforme aux catégories d'entraînement."
    )
    PropertyType: str = Field(
        min_length=1,
        max_length=150,
        description="Type de propriété exactement conforme aux catégories d'entraînement."
    )
    Decade: int = Field(
        strict=True,
        ge=DECADE_MIN,
        le=DECADE_MAX,
        description="Décénnie de construction."
    )
    Surface: float = Field(
        strict=True,
        gt=SURFACE_MIN,
        le=SURFACE_MAX,
        description="Surface totale du bâtiment."
    )

    @field_validator("BuildingType")
    @classmethod
    def validate_building_type(cls, value: str) -> str:
        if value not in ALLOWED_BUILDING_TYPES:
            raise ValueError(
                f"BuildingType invalide : {value!r}. "
                f"Valeurs autorisées : {sorted(ALLOWED_BUILDING_TYPES)}"
            )
        return value

    @field_validator("PropertyType")
    @classmethod
    def validate_property_type(cls, value: str) -> str:
        if value not in ALLOWED_PROPERTY_TYPES:
            raise ValueError(
                f"PropertyType invalide : {value!r}. "
                f"Valeurs autorisées : {sorted(ALLOWED_PROPERTY_TYPES)}"
            )
        return value

    @model_validator(mode="after")
    def validate_business_rules(self) -> "PredictionInput":
        current_year = date.today().year

        if self.Decade > current_year:
            raise ValueError(
                f"Decade={self.Decade} est dans le futur."
            )

        if self.Surface < 10:
            raise ValueError(
                "Surface trop faible pour un enregistrement bâtiment crédible."
            )

        return self


class PredictionOutput(BaseModel):
    prediction: float
