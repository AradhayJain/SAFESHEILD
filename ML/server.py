# app.py

from flask import Flask, request, jsonify, send_file
from util_training import get_model
import os

app = Flask(__name__)

@app.route('/train_model', methods=['POST'])
def train_model():
    try:
        data = request.json
        user_id = data.get("user_id")
        features = data.get("data")

        if not user_id or not features:
            return jsonify({"error": "Missing user_id or data"}), 400

        model_path = get_model(user_id, features)

        return jsonify({"model_path": model_path}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
