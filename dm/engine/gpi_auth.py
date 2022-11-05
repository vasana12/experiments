import json
import math

import sys

import requests
import time

from dm.engine.exceptions import RapidApiError, LamadavaServerError, NoUserIdException, InstagramLoginError, \
    AccountException
from instagrapi import Client
import logging


from db import m_instagram
from dm.execute.run_select_influencer import get_influnecer_info_by_project, search_influencer_info
from dm.prepare import get_dm_source, get_influencer
from instagrapi.exceptions import UserNotFound
from instagrapi.types import User

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



def login_by_lamadava(username,password):
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

def login_v_gpi(client:Client, username, password):
    try_num = 0
    max_login_try_num = 2

    while True:
        if try_num >= max_login_try_num:
            logger.error(f"로그인 실패 다른 아이디로 로그인")
            raise InstagramLoginError
        # access_key = "PHqrL750D4xvF5h27UdWDMTnXs8fhTPx"
        # headers = {"x-access-key": access_key}
        # data = {"username": username, "password": password}

        try:
            is_login = client.login(username=username, password=password)

        except Exception as e:
            try_num += 1
            logger.warning(f" 로그인 시도 {try_num} 번째 실패함 {e}// {e.__class__.__name__}- username:{username} password:{password}")
            continue

        if not is_login:
            try_num += 1
            logger.warning(f"로그인 시도 {try_num} 번째 실패함 - username:{username} password:{password}")
            continue
        logger.info(f"로그인 성공 username:{username} password:{password}")
        return True

def login_by_sessionid_v_gpi(client, sessionid):
    try_num = 0
    max_login_try_num=2
    while True:

        if try_num >= max_login_try_num:
            logger.error(f"로그인 실패 다른 아이디로 로그인")
            raise InstagramLoginError
        # access_key = "PHqrL750D4xvF5h27UdWDMTnXs8fhTPx"
        # headers = {"x-access-key": access_key}
        # data = {"username": username, "password": password}

        try:
            is_login = client.login_by_sessionid(sessionid)
        except Exception as e:
            try_num += 1
            logger.warning(
                f" 로그인 시도 {try_num} 번째 실패함 {e}// {e.__class__.__name__}- sessionid:{sessionid} ")
            continue

        if not is_login:
            try_num += 1
            logger.warning(f"로그인 시도 {try_num} 번째 실패함 - sessionid:{sessionid} ")
            continue
        logger.info(f"로그인 성공 sessionid:{sessionid} ")
        return True

def login_by_session_v_lamadava(session_id, username=None, password=None):
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

def login_v_lamadava(username,password):
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
def select_user(username=None, client_name=None, max_messages_per_day=None):
    if username:
        account_setting_info = INSTA_ACCOUNT_OBJ.select_and_update_user(username=username, client_name=None)
    else:
        account_setting_info = INSTA_ACCOUNT_OBJ.select_and_update_user(username=None, client_name=None)

    if account_setting_info is None:
        logger.info("no account available")
        return None
    else:
        logger.info(f"account is selected:{account_setting_info['username']}/{account_setting_info['password']}")

        return account_setting_info