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
        checkpoint = self.db_conn["account"]["checkpoint"].find_one({"username":self.api.username})
        return (checkpoint["total"], checkpoint["blocked_actions"], checkpoint["total_requests"], checkpoint["start_time"])
    except Exception:
        pass
    return None

def save_checkpoint(self:instamanager.Bot):
    checkpoint = Checkpoint(self)
    total, blocked_actions, total_requests, start_time = checkpoint.dump()

    checkpoint_collection = self.db_conn["account"]["checkpoint"]

    if checkpoint_collection.count({"username":self.api.username}) > 0:
        checkpoint_collection.update_one(filter={"username": self.api.username},
                                         update={"$set":
                                             {
                                                 "username": self.api.username,
                                                 "total": total,
                                                 "blocked_actions": blocked_actions,
                                                 "total_requests": total_requests,
                                                 "start_time": start_time
                                             }}, upsert=True
                                         )

        return True

    checkpoint_collection.insert(
        {
            "username": self.api.username,
            "total": total,
            "blocked_actions": blocked_actions,
            "total_requests": total_requests,
            "start_time": start_time
        }
    )
    return True



