# model_trainer.py (extend this file)

import joblib
import numpy as np
import os

# {"result": [1]}   // Genuine
# or
# {"result": [-1]}  // Anomaly


def predict_with_model(user_id, data_dict, model_dir="ML/models"):
    model_path = os.path.join(model_dir, f"{user_id}_ocsvm.pkl")
    if not os.path.exists(model_path):
        raise FileNotFoundError("Model for user not found")

    model = joblib.load(model_path)
    X = np.array([list(values) for values in zip(*data_dict.values())])
    return model.predict(X).tolist()
