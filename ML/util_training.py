import numpy as np
from sklearn.svm import OneClassSVM
import joblib
import os

def preprocess_data(data_dict):
    """
    Converts the input dictionary into a NumPy array for training.
    Assumes each key maps to a list of equal-length feature vectors.
    """
    try:
        return np.array([list(values) for values in zip(*data_dict.values())])
    except Exception as e:
        raise ValueError(f"Failed to preprocess data: {e}")

def train_one_class_svm(X, gamma='auto', nu=0.1):
    """
    Trains a One-Class SVM model on the given data.
    """
    model = OneClassSVM(gamma=gamma, nu=nu)
    model.fit(X)
    return model

def save_model(model, user_id, model_dir="ML/models"):
    """
    Serializes the trained model and saves it as a pickle file.
    """
    os.makedirs(model_dir, exist_ok=True)
    filename = os.path.join(model_dir, f"{user_id}_ocsvm.pkl")
    joblib.dump(model, filename)
    return filename



def get_model(user_id, data_dict):
    """
    Takes user data and returns the path to the saved trained model.
    """
    X = preprocess_data(data_dict)
    model = train_one_class_svm(X)
    model_path = save_model(model, user_id)
    return model_path

def main(user_id, data_dict):
    """
    Main function to process input data, train model, and save it.
    """
    print("[*] Preprocessing data...")
    X = preprocess_data(data_dict)
    
    print("[*] Training One-Class SVM model...")
    model = train_one_class_svm(X)
    
    print("[*] Saving model...")
    save_model(model, user_id)

if __name__ == "__main__":
    # Simulated input data (replace with real input)
    example_data = {
        "typing_speed": [3.2, 2.9, 3.1, 3.0, 3.3],
        "touch_duration": [100, 120, 110, 105, 115]
    }
    
    user_id = "user123"
    main(user_id, example_data)
