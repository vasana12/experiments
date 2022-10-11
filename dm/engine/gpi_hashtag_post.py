import json
import math
import requests
from instagrapi import Client
import logging

from instagrapi.extractors import extract_media_v1
from instagrapi.types import DirectMessage, Media
from db import m_instagram
from dm.engine import completed_target_influencer
from dm.engine.exceptions import *
from dm.execute.run_select_influencer import search_influencer_info, get_influnecer_user_id_by_project
from dm.prepare import get_dm_source
FORMAT = '%(module)s.%(funcName)s - %(message)s - %(levelname)s - %(asctime)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)
if logger.hasHandlers():
    # Logger is already configured, remove all handlers
    logger.handlers = []
logger.setLevel(logging.INFO)

host, port, proxy_username, proxy_password = "resi3.ipb.cloud", "9000", "MrIlCvzYImHc0I3t", "wifi;us;;;;"
proxy = f"http://{proxy_username}:{proxy_password}@{host}:{port}"

db_conn = m_instagram.InstaDB().conn
INSTA_ACCOUNT_OBJ = m_instagram.InstaAccount(channel_name="instagram")
INSTA_ACCOUNT_OBJ.client_name = "admin_test"
max_messages_per_day = 200
max_group_size = 30
client = Client()
proxy = None
client.set_proxy(dsn=proxy)

def select_user(username=None, max_messages_per_day=None):
    account_setting_info = INSTA_ACCOUNT_OBJ.select_and_update_user(username=username)
    if not account_setting_info:
        logger.info("no account available")
        return None
    else:
        logger.info(f"account is selected:{account_setting_info['username']}/{account_setting_info['password']}")
        return account_setting_info

def login_by_session(session_id, username=None, password=None):
    pass
    # access_key = "nTYC9RbjpV8axJ3I9OnKI9Z4QVu7hzrE"
    # headers = {"x-access-key": access_key}
    # data = {"sessionid": session_id}
    # url = "https://api.lamadava.com/s1/auth/login/by/sessionid"
    # response = requests.post(url=url, data=data, headers=headers)
    # data = json.loads(response.text)
    # try_num = 0
    # while True:
    #     if try_num >=5:
    #         return None
    #     if type(data) is not str:
    #         print(data)
    #         logger.error(f"session return error - username:{username}/password:{password}, session_id:{session_id}")
    #         try_num += 1
    #         continue
    #     logger.info(f"session return success - username:{username}/password:{password}, session_id:{session_id}")
    #     return response

def login(username, password):
    try_num = 0
    while True:
        if try_num >= 3:
            logger.error(f"로그인 실패 다른 아이디로 로그인")
            return None
        # access_key = "PHqrL750D4xvF5h27UdWDMTnXs8fhTPx"
        # headers = {"x-access-key": access_key}
        # data = {"username": username, "password": password}

        is_login = client.login(username=username, password=password)
        if not is_login:
            try_num += 1
            logger.error(f"로그인 시도 {try_num} 번째 실패함 - username:{username} password:{password}")
            continue

        logger.fatal(f"로그인 성공 username:{username} password:{password}")
        return True

def infinite_login(username, max_messages_per_day, session_id=None):
    while True:
        ##1. 사용할 계정 DB 에서 가져오기
        account_setting_info = select_user(username=username, max_messages_per_day=max_messages_per_day)
        if account_setting_info is None:
            logger.fatal("infinite_login_end")
            return None

        ##2. 가져온 계정으로 로그인 시도. session 받아오기
        if session_id:
            login_session = login_by_session(session_id)
        else:
            login_session = login(account_setting_info["username"], account_setting_info["password"])

        ##2.1 가져온 계정으로 로그인이 성공한 경우 받아온 session을 return 해준다
        if login_session:
            account_setting_info.update(graph_session=client.sessionid)
            return account_setting_info

        ##2.2 가져온 계정으로 로그인이 실패한 경우 계정을 새로 가져온다.
        else:
            continue

def get_user_by_id(user_id):
    try:
        access_key = "nTYC9RbjpV8axJ3I9OnKI9Z4QVu7hzrE"
        headers = {"x-access-key": access_key}
        params = {"id": user_id}
        response = requests.get(url="https://api.lamadava.com/v1/user/by/id", params=params, headers=headers)
        json_data = json.loads(response.text)
    except Exception as e:
        logger.error(f"user_id:{user_id}/error:{e}")
        return None
    else:
        if json_data.get("pk") is None:
            logger.info(f"json_data:{json_data}")
            return None
        return json_data

def get_valid_user_ids(user_ids):
    user_ids = list(filter(lambda x: get_user_by_id(x), user_ids))
    return user_ids
#
def get_posts(name, max_amount,tab_key, max_id):
    access_key = "nTYC9RbjpV8axJ3I9OnKI9Z4QVu7hzrE"
    headers = {"x-access-key": access_key}
    params = {"name": name, "max_amount": max_amount, "max_id": max_id}

    try:
        response = requests.get(url=f"https://api.lamadava.com/v1/hashtag/medias/{tab_key}/chunk", params=params, headers=headers)

        json_data = json.loads(response.text)
        medias = json_data[0]
        max_id = json_data[-1]

    except Exception as e:
        logger.error(f"name:{max_id}/error:{e.__class__.__name__}/{response.text}")
        return None
    else:
        return medias, max_id

def run(name, max_amount, tab_key):
    max_id = None
    while True:
        medias, max_id = get_posts(name=name, max_amount=max_amount,  tab_key=tab_key, max_id=max_id)
        print("max_id:", max_id)
        if max_id is None:
            break
        for media in medias:
            yield media

def divide_user_infos_list(user_infos_list, group_size):
    # user_infos_list = list(map(lambda x: [x] if type(x) is not list else x, user_infos_list))
    total_user_infos_group = []
    group_size = min(max_group_size, group_size)

    total_user_infos_group_count = len(user_infos_list) / group_size
    total_user_infos_group_count = math.ceil(total_user_infos_group_count)

    logger.info(f"total_user_infos_group_count:{total_user_infos_group_count}")

    for i in range(0, total_user_infos_group_count):
        prev_page = group_size * i
        next_page = group_size * (i + 1)
        total_user_infos_group.append(user_infos_list[prev_page:next_page])
    return total_user_infos_group


if __name__ == "__main__":
    ##project 이름 과 제외할 프로젝트 이름
    name = "고구마"
    max_amount = 27
    tab_key = "top"
    for idx, media in enumerate(run(name=name, max_amount=max_amount, tab_key=tab_key)):
        extract_media_v1(media)

        # input()


