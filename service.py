from __future__ import annotations

import pandas as pd
import bentoml
from bentoml.models import BentoModel

from schemas import PredictionInput, PredictionOutput


image = (
    bentoml.images.Image(python_version="3.11")
    .python_packages(
        "bentoml",
        "scikit-learn",
        "pandas",
        "numpy",
        "pydantic>=2,<3",
    )
)


@bentoml.service(
    image=image,
    resources={"cpu": "1", "memory": "512Mi"},
    traffic={"timeout": 30},
)
class EnergyService:
    model_ref = BentoModel("seattle_energy_model:latest")

    def __init__(self) -> None:
        self.model = bentoml.sklearn.load_model(self.model_ref)

    @bentoml.api(
        route="/predict",
        input_spec=PredictionInput,
        output_spec=PredictionOutput,
    )
    def predict(self, payload: PredictionInput) -> PredictionOutput:
        X = pd.DataFrame([payload.model_dump()])
        pred = self.model.predict(X)[0]
        return PredictionOutput(prediction=float(pred))        
