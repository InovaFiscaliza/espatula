import os
from fastcore.xtras import Path, listify
import numpy as np
from joblib import load

from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv(), override=True)


class SGD:
    def __init__(self, model_path=os.environ.get("MODEL_SGD")):
        try:
            self.model_path = model_path
            self.model = load(model_path)
        except FileNotFoundError as e:
            raise FileNotFoundError(f"Model not found at {model_path}") from e

    def predict(self, X):
        predicted_class = self.model.predict(X)
        predicted_proba = self.model.predict_proba(X)[:, 1]
        return np.column_stack((predicted_class, predicted_proba))
