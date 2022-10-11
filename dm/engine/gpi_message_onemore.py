import json
import math

import sys

import requests
import time
from instagrapi import Client
import logging


from db import m_instagram
from dm.engine.exceptions import *
from dm.execute.run_select_influencer import get_influnecer_info_by_project, search_influencer_info
from dm.prepare import get_dm_source, get_influencer

FORMAT = '%(module)s.%(funcName)s - %(message)s - %(levelname)s - %(asctime)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)
if logger.hasHandlers():
    # Logger is already configured, remove all handlers
    logger.handlers = []
logger.setLevel(logging.INFO)



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
            account_setting_info.update(graph_session=login_session)
            return account_setting_info

        ##2.2 가져온 계정으로 로그인이 실패한 경우 계정을 새로 가져온다.
        else:
            continue

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
        return json_data
def get_valid_user_ids(user_ids):
    user_ids = list(filter(lambda x: get_user_by_id(x), user_ids))
    return user_ids
def send_message(user_infos, next_account_info=None):

    max_account_retry_num=3
    max_request_retry_num=3
    request_retry_num = 0
    account_retry_num = 0

    ###next_account_info 가 없으면 계정을 가져오기 있으면 해당 계정을 사용한다.
    account_info = infinite_login(username=None, max_messages_per_day=max_messages_per_day, session_id=None) if next_account_info is None else next_account_info
    # if account_info is None:
    #     raise ValueError

    user_ids = list(map(lambda x: x["userid"], user_infos))
    user_ids = get_valid_user_ids(user_ids)

    logger.info(f"get_valid_user_ids:{user_ids}")
    while True:
        if account_retry_num>=max_account_retry_num:
            raise AccountRetryExcessException
        access_key = "nTYC9RbjpV8axJ3I9OnKI9Z4QVu7hzrE"
        headers = {"x-access-key": access_key}
        sessionid = account_info.get('graph_session')
        username = account_info.get('username')
        password = account_info.get('password')

        text = get_dm_source.get_source_message(filename="rounded.txt")

        data = {"sessionid": sessionid, "user_ids": user_ids, "text": f"{text}"}
        url = "https://api.lamadava.com/s1/direct/send"
        logger.info(f"prepare_request//data:{data}")

        response = requests.post(url=url, data=data, headers=headers)

        try:
            json_data = json.loads(response.text)
        except Exception as e:
            request_retry_num += 1
            ### request 가 max retry 를 초과했을 때 다른 아이디로 로그인 해준다. request_retry_num -> 0 , account_retry_num += 1
            if request_retry_num >= max_request_retry_num:
                logger.error(f"json loads error:{e}, retry login // account_retry_num :{account_retry_num}")
                request_retry_num = 0
                account_retry_num += 1
                account_info = infinite_login(username=None, max_messages_per_day=max_messages_per_day, session_id=None)
                continue
            logger.error(f"json loads error, retry request // request_retry_num :{request_retry_num}")
            continue

        if json_data:
            if "thread_id" not in json_data.keys():
                request_retry_num += 1
                ### request 가 max retry 를 초과했을 때 다른 아이디로 로그인 해준다. request_retry_num -> 0 , account_retry_num += 1
                if request_retry_num >= max_request_retry_num:
                    logger.error(f"undefined error :{json_data}, retry login // account_retry_num :{account_retry_num}")
                    request_retry_num = 0
                    account_retry_num += 1
                    account_info = infinite_login(username=None, max_messages_per_day=max_messages_per_day,
                                                  session_id=None)
                    continue
                logger.error(f"challenge_required, retry request // request_retry_num :{request_retry_num}")
                continue

        if "challenge_required" in response.text:
            request_retry_num += 1
            ### request 가 max retry 를 초과했을 때 다른 아이디로 로그인 해준다. request_retry_num -> 0 , account_retry_num += 1
            if request_retry_num >=max_request_retry_num:
                logger.error(f"challenge_required, retry login // account_retry_num :{account_retry_num}")
                request_retry_num = 0
                account_retry_num += 1
                account_info = infinite_login(username=None, max_messages_per_day=max_messages_per_day, session_id=None)
                continue
            logger.error(f"challenge_required, retry request // request_retry_num :{request_retry_num}")
            continue

        if "Bad gateway" in response.text:
            request_retry_num += 1

            ### request 가 Max retry 를 초과했을 때 다른 아이디로 로그인 해준다. request_retry_num -> 0, account_retry_num += 1
            if request_retry_num >= max_request_retry_num:
                logger.error(f"Bad gateway,  retry login //account_retry_num :{account_retry_num}")
                request_retry_num = 0
                account_retry_num += 1
                account_info = infinite_login(username=None, max_messages_per_day=max_messages_per_day, session_id=None)
                continue
            logger.error(f"Bad gateway,  retry request //request_retry_num :{request_retry_num}")
            continue
        if "item_ack" in response.text:
            request_retry_num += 1

            ### request 가 Max retry 를 초과했을 때 다른 아이디로 로그인 해준다. request_retry_num -> 0, account_retry_num += 1
            if request_retry_num >= max_request_retry_num:
                logger.error(f"Bad gateway,  retry login //account_retry_num :{account_retry_num}")
                request_retry_num = 0
                account_retry_num += 1
                account_info = infinite_login(username=None, max_messages_per_day=max_messages_per_day, session_id=None)
                continue
            logger.error(f"Bad gateway,  retry request //request_retry_num :{request_retry_num}")
            continue

        if "item_ack" in response.text:
            request_retry_num += 1

            ### request 가 Max retry 를 초과했을 때 다른 아이디로 로그인 해준다. request_retry_num -> 0, account_retry_num += 1
            if request_retry_num >= max_request_retry_num:
                logger.error(f"Bad gateway,  retry login //account_retry_num :{account_retry_num}")
                request_retry_num = 0
                account_retry_num += 1
                account_info = infinite_login(username=None, max_messages_per_day=max_messages_per_day, session_id=None)
                continue
            logger.error(f"Bad gateway,  retry request //request_retry_num :{request_retry_num}")
            continue

        ###dm 발송 성공

        logger.info(f"username:{username} /password:{password}/ sessionid:{sessionid} -> user_info:{user_infos} /response:{response.text}")

        INSTA_ACCOUNT_OBJ.account_collection.update_one({"useraname": account_info["username"]}, {"$inc": {"usage.dm": 1}})
        account_info["usage"]["dm"] += 1
        next_account_info = account_info if account_info["usage"]["dm"]<max_messages_per_day else None
        time.sleep(10)
        return next_account_info

def get_user():

    ##파일이름
    filename = "라운디드"

    ##제외할프로젝트 설정
    exclude_username_list = get_influnecer_info_by_project(project_name="rounded", only_username=True)

    ##제외할 단어 설정
    exclude_word = "official"

    ##타겟 해시태그 설정 해시태그
    search_hashtag = get_dm_source.get_source_hashtag("rounded.txt")
    # search_hashtag = "제주도 제테크 투자 골프스타그램 스크린골프 골프웨어 골프중독 라운딩 라운딩패션 골프화 골프레슨 스포츠 공구 공구진행 협찬 베이비 2살 3살 10개월"

    ##몇개 가져올지 설정
    skip = 1500
    limit = 3000
    only_username = False


    target_username_list = search_influencer_info(search_hashtag=search_hashtag, skip=skip, limit=limit,
                                                  only_username=only_username, filename=filename,
                                                  exclude_user_list=exclude_username_list)
    target_username_list = list(filter(lambda x: exclude_word not in x["username"], target_username_list))
    target_username_list = list(map(lambda x: {"userid": int(x["userid"]) if "userid" in x.keys() else None, "username": x["username"] if "username" in x.keys() else None}, target_username_list))

    target_username_list = list(filter(lambda x: x is not None, target_username_list))
    print(target_username_list)
    # print(len(target_username_list))
    return target_username_list

if __name__ == "__main__":

    user_infos_list = get_user()
    user_infos_list = list(map(lambda x: [x] if type(x) is not list else x, user_infos_list))
    max_messages_per_day = 200
    username = None
    password = None

    next_account_info = None

    while user_infos_list:
        ## user_infos_list 중 첫번째 리스트를 뽑아서 메세지 발송
        target_user_infos = user_infos_list.pop(0)
        logger.info(f"target_user_infos:{target_user_infos}")
        next_account_info = send_message(user_infos=target_user_infos, next_account_info=next_account_info)
        # try:
        #     next_account_info = send_message(user_infos=target_user_infos, next_account_info=next_account_info)
        # except Exception as e:
        #     logger.error(f"error:{e}, type(e): {type(e)}")
        #     input()
        #     if isinstance(e, AccountException):
        #         continue
        #     else:
        #         continue
        ##발송 결과가 200 이 아닐때 response error num 값을 1 올려준다 . 5번 이상 연속 에러 발생시 새로 로그인한다.

    # "54972950573%3AHz4UiDsvtNXifR%3A26%3AAYci83thKFN8r29UL_htrCtVptbIffa-IIqrtObExw"
    # send_message(session_id)
