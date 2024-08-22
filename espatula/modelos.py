import os
from functools import cached_property
from pathlib import Path

import numpy as np
from dotenv import find_dotenv, load_dotenv
from joblib import load

load_dotenv(find_dotenv(), override=True)


class SGD:
    def __init__(self, model_path=os.environ.get("MODEL_SGD")):
        if (model_path := Path(model_path)).is_file():
            assert model_path.suffix == ".joblib", "Model must be a .joblib file"
        self.model_path = model_path

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
