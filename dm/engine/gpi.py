import json
import math

import sys

import requests
import time
from instagrapi import Client
import logging


from db import m_instagram
from dm.execute.run_select_influencer import get_influnecer_info_by_project, search_influencer_info
from dm.prepare import get_dm_source, get_influencer

FORMAT = '%(module)s.%(funcName)s - %(message)s - %(levelname)s - %(asctime)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)
if logger.hasHandlers():
    # Logger is already configured, remove all handlers
    logger.handlers = []
logger.setLevel(logging.INFO)
access_key = "nTYC9RbjpV8axJ3I9OnKI9Z4QVu7hzrE"
headers = {"x-access-key": access_key}

db_conn = m_instagram.InstaDB().conn
INSTA_ACCOUNT_OBJ = m_instagram.InstaAccount(channel_name="instagram")
INSTA_ACCOUNT_OBJ.client_name = "admin_test"


def select_user(username=None, max_messages_per_day=None):
    account_setting_info = INSTA_ACCOUNT_OBJ.select_and_update_user(username=username)
    if not account_setting_info:
        logger.info("no account available")
        return None
    else:
        logger.info(f"account is selected:{account_setting_info['username']}/{account_setting_info['password']}")
        return account_setting_info


def get_user_by_id(user_id):
    params = {"id": user_id}
    response = requests.get(url="https://api.lamadava.com/v1/user/by/id", params=params, headers=headers)
    json_data = json.loads(response.text)
    return json_data

def login_by_session(session_id, username=None, password=None):
    pass
    access_key = "nTYC9RbjpV8axJ3I9OnKI9Z4QVu7hzrE"
    headers = {"x-access-key": access_key}
    data = {"sessionid": session_id}
    url = "https://api.lamadava.com/s1/auth/login/by/sessionid"
    response = requests.post(url=url, data=data, headers=headers)
    data = json.loads(response.text)
    try_num = 0
    while True:
        if try_num >=5:
            return None
        if type(data) is not str:
            print(data)
            logger.error(f"session return error - username:{username}/password:{password}, session_id:{session_id}")
            try_num += 1
            continue
        logger.info(f"session return success - username:{username}/password:{password}, session_id:{session_id}")
        return response

def login(username,password):
    try_num = 0
    while True:
        if try_num >= 20:
            logger.error(f"lamada - login max_try_num:{try_num}")
            return None
        access_key = "PHqrL750D4xvF5h27UdWDMTnXs8fhTPx"
        headers = {"x-access-key": access_key}
        data = {"username": username, "password": password}
        url = "https://api.lamadava.com/s1/auth/login"
        response = requests.post(url=url, data=data, headers=headers)

        try:
            data = json.loads(response.text)
        except Exception as e:

            logger.error(f"{e}/try_num:{try_num}")
            continue

        if type(data) is not str:
            try_num += 1
            logger.error(f"{data}/try_num:{try_num}")
            continue

        logger.fatal(f"login:{username}/{password}/ sessionid - {data}")
        return data

def send_messages(session_id, user_ids, text, max_messages_per_day):
    access_key = "nTYC9RbjpV8axJ3I9OnKI9Z4QVu7hzrE"
    headers = {"x-access-key": access_key}
    user_ids = list(map(lambda x: str(x), user_ids))
    user_ids = list(set(user_ids))
    print(f"user_ids : {len(user_ids)}")

    for idx, user_id in enumerate(user_ids):
        data = {"sessionid": session_id, "user_ids": [user_id], "text": f"{text}", }
        url = "https://api.lamadava.com/s1/direct/send"
        response = requests.post(url=url, data=data, headers=headers)
        print(idx, user_id, response.text)
        time.sleep(10)

        if idx == max_messages_per_day:
            broken_items = user_ids[user_ids.index(user_id):]
            return broken_items

def send_message(account_info, user_info_list):
    max_retry_num=1
    retry_num = 0
    while True:
        if retry_num>=max_retry_num:
            return 400
        access_key = "nTYC9RbjpV8axJ3I9OnKI9Z4QVu7hzrE"
        headers = {"x-access-key": access_key}
        sessionid = account_info.get('graph_session')
        username = account_info.get('username')
        password = account_info.get('password')

        text = get_dm_source.get_source_message(filename="rounded.txt")
        userid_list = list(map(lambda x: x["userid"], user_info_list))
        data = {"sessionid": sessionid, "user_ids": userid_list, "text": f"{text}"}
        url = "https://api.lamadava.com/s1/direct/send"
        response = requests.post(url=url, data=data, headers=headers)

        if "challenge_required" in response.text:
            return 400
        if "Bad gateway" in response.text:
            return 400

        if "item_ack" in response.text:
            retry_num+=1
            logger.error(f"item_ack, retry:{retry_num}")
            continue

        time.sleep(10)
        logger.info(f"username:{username} /password:{password}/ sessionid:{sessionid} -> user_info:{user_info_list} /response:{response.text}")
        return 200

