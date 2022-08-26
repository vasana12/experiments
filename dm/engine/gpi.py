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
    skip = 3000
    limit = 6000
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
    MAX_MESSAGE_PER_THREAD = 30
    user_info_list = get_user()
    divided_user_info_list= []
    total_required_thread = len(user_info_list) / MAX_MESSAGE_PER_THREAD
    total_required_thread = math.ceil(total_required_thread)

    logger.info(f"total_required_thread:{total_required_thread}")

    for i in range(0, total_required_thread):
        prev_page = MAX_MESSAGE_PER_THREAD * i
        next_page = MAX_MESSAGE_PER_THREAD * (i + 1)
        divided_user_info_list.append(user_info_list[prev_page:next_page])

    # response = login_by_session("54643180776%3AjN9IuooPqRIGwA%3A16%3AAYfmOkeGnahb0uK9PViSOMf5_DTQcGcgSSWYx3CBIA")

    max_messages_per_day = 200
    username = None
    password = None

    account_info = infinite_login(username = None, max_messages_per_day=max_messages_per_day, session_id=None)

    if account_info is None:
        sys.exit()

    #유저리스트에 대해 디엠 발송 시작
    response_error_num = 0

    idx = 0
    while True:
        idx += 1
        ##max_messages_per_day 를 초과하면 다른 아이디로 로그인 시켜준다.
        if idx != 0 and idx%max_messages_per_day == 0:
            logger.info(f"idx-{idx} 한도 초과. 다른 아이디로 로그인 ")
            account_info = infinite_login(username= None, max_messages_per_day=max_messages_per_day)
            response_error_num=0
        ##메세지 발송
        res = send_message(account_info=account_info, user_info_list=user_info_list)

        ##발송 결과가 200 이 아닐때 response error num 값을 1 올려준다 . 5번 이상 연속 에러 발생시 새로 로그인한다.
        if res != 200:
            response_error_num += 1
            logger.info(f"response_error_num: {response_error_num}")
            if response_error_num >= 3:
                logger.info(f"idx-{idx} 에러 발생함. response_error_num: {response_error_num}새로운 아이디로 로그인")
                account_info = infinite_login(username=None, max_messages_per_day=max_messages_per_day)
            continue

        ##발송 결과가 200 인 경우
        else:
            logger.info(f"idx-{idx} 200.")
            response_error_num = 0

    # "54972950573%3AHz4UiDsvtNXifR%3A26%3AAYci83thKFN8r29UL_htrCtVptbIffa-IIqrtObExw"
    # send_message(session_id)
