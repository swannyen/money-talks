from typing import Literal, get_args

AcceptedActions = Literal["FEE", "BUY", "SELL", "DIVIDEND", "DEPOSIT"]


def is_valid_action(action):
    return action in get_args(AcceptedActions)
