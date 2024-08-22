from functools import cached_property
from pathlib import Path

import numpy as np
from joblib import load


MODEL_SGD = "https://github.com/InovaFiscaliza/dados-pacp/raw/main/model_trainning/clf_mktplaces_3/clf_marketplaces_scikit-learn-1.5.1.joblib"


class SGD:
    def __init__(self, model_path=MODEL_SGD):
        self.model_path = Path(model_path)

    @cached_property
    def model(self):
        try:
            return load(self.model_path)
        except Exception as e:
            raise Exception(f"Error loading model: {e}")

    def predict(self, X):
        predicted_class = self.model.predict(X)
        predicted_proba = self.model.predict_proba(X)[:, 1]
        return np.column_stack((predicted_class, predicted_proba))
