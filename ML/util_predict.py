from Swiping.predict_swipe_risk import SwipeRiskPredictor
from Swiping.update_model import SwipeModelUpdater 
from Typing.predict_typing_risk import TypingRiskPredictor
from Typing.update_model import TypingModelUpdater
from typing import List

import numpy as np


def flatten_swiping_data(data: dict) -> List[float]:
    return [value[0] for value in data.values()]


def convert_to_native(obj):
    if isinstance(obj, dict):
        return {k: convert_to_native(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_native(v) for v in obj]
    elif isinstance(obj, (np.bool_, np.int_, np.float_)):
        return obj.item()
    else:
        return obj


def predict_with_model(user_id, data_dict):
    response = {}

    if 'swiping' in data_dict:
        response['swiping'] = predict_swiping(user_id, flatten_swiping_data(data_dict['swiping']))

    if 'typing' in data_dict:
        response['typing'] = predict_typing(user_id, flatten_swiping_data(data_dict['typing']))

    return response


def predict_swiping(user_id, data):
    srp = SwipeRiskPredictor()
    prediction_res = srp.predict_swipe_risk(user_id, data)

    smu = SwipeModelUpdater()
    model_updation = smu.update_swipe_model_if_appropriate(user_id, data, prediction_res)

    return {
        'prediction_result': convert_to_native(prediction_res),
        'model_updation': convert_to_native(model_updation)
    }


def predict_typing(user_id, data):
    trp = TypingRiskPredictor()
    prediction_res = trp.predict_risk(user_id, data)

    tmu = TypingModelUpdater()
    model_updation = tmu.update_model_if_appropriate(user_id, data, prediction_res)

    return {
        'prediction_result': convert_to_native(prediction_res),
        'model_updation': convert_to_native(model_updation)
    }

