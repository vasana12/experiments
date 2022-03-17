"""
    Instabot Checkpoint methods.
"""
from __future__ import annotations

import time
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    import instamanager
import os
import pickle
from datetime import datetime

current_path = os.path.abspath(os.getcwd())
CHECKPOINT_PATH = current_path + "/config/{fname}.checkpoint"


class Checkpoint(object):
    """
        Checkpoint for instabot.Bot class which can store:
            .total[<name>] - all Bot's counters
            .blocked_actions[<name>] - Bot's blocked actions
            .following (list of user_ids)
            .followers (list of user_ids)
            .date (of checkpoint creation)
    """
    def __init__(self, bot):
        self.total = {}
        for k in bot.total:
            self.total[k] = bot.total[k]
        self.blocked_actions = {}
        for k in bot.blocked_actions:
            self.blocked_actions[k] = bot.blocked_actions[k]
        self.start_time = bot.start_time
        self.date = datetime.now()
        self.total_requests = bot.api.total_requests
        # self.bot = bot

    def fill_following(self, bot):
        self._following = [item["pk"] for item in bot.api.get_total_self_followings()]

    def fill_followers(self, bot):
        self._followers = [item["pk"] for item in bot.api.get_total_self_followers()]

    def dump(self):
        return (self.total, self.blocked_actions, self.total_requests, self.start_time)


def load_checkpoint(self:instamanager.Bot):
    try:
        account = self.db_conn["account"].find_one({"username":self.api.username})
        return (account["checkpoint"]["total"], account["checkpoint"]["blocked_actions"], account["checkpoint"]["total_requests"], account["checkpoint"]["start_time"])
    except Exception:
        pass
    return None

def save_checkpoint(self:instamanager.Bot):
    checkpoint = Checkpoint(self)
    total, blocked_actions, total_requests, start_time = checkpoint.dump()

    account_collection = self.db_conn["account"]["account"]


    account_collection.update_one(filter={"username": self.api.username},
                                         update={"$set":
                                             {
                                                 "checkpoint.username": self.api.username,
                                                 "checkpoint.total": total,
                                                 "checkpoint.blocked_actions": blocked_actions,
                                                 "checkpoint.total_requests": total_requests,
                                                 "checkpoint.start_time": start_time
                                             }
                                         }
                                         )

    return True



