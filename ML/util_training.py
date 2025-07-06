from Swiping.model import SwipeModelTrainer
from Typing.model import TypingModelTrainer
import pandas as pd


def get_model(user_id, data_dict):
    """
    Trains models for the given user using swiping and/or typing data.

    """
    response = {}

    if 'swiping' in data_dict:
        swiping_df = pd.DataFrame.from_dict(data_dict['swiping'])
        swipe_trainer = SwipeModelTrainer()
        response['swiping'] = swipe_trainer.train_swipe_model_from_dataframe(user_id, swiping_df)

    if 'typing' in data_dict:
        typing_df = pd.DataFrame.from_dict(data_dict['typing'])
        typing_trainer = TypingModelTrainer()
        response['typing'] = typing_trainer.train_typing_model_from_dataframe(user_id, typing_df)

    return response
