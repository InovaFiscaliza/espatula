from functools import cached_property
from pathlib import Path

import numpy as np
from joblib import load


MODEL_SGD = "https://github.com/InovaFiscaliza/dados-pacp/raw/main/model_trainning/clf_mktplaces_3/clf_marketplaces_scikit-learn-1.5.1.joblib"


class SGD:
    def __init__(self, model_path=MODEL_SGD):
        self.model_path = model_path
        self.local_model_path = (
            Path(__file__).parent.parent / "modelos" / "model.joblib"
        )

        if not self.local_model_path.exists():
            self.local_model_path.parent.mkdir(parents=True, exist_ok=True)
            self._download_model()

    def _download_model(self):
        import requests

        response = requests.get(self.model_path)
        response.raise_for_status()

        with open(self.local_model_path, "wb") as f:
            f.write(response.content)

    @cached_property
    def model(self):
        try:
            return load(self.local_model_path)
        except Exception as e:
            raise Exception(f"Error loading model: {e}")

    def predict(self, X):
        predicted_class = self.model.predict(X)
        predicted_proba = self.model.predict_proba(X)[:, 1]
        return np.column_stack((predicted_class, predicted_proba))
