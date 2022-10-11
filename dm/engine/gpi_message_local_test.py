import json
import math
import sys
import requests
import time
from instagrapi import Client
import logging
from instagrapi.types import DirectMessage
from db import m_instagram
from dm.engine import completed_target_influencer
from dm.engine.exceptions import *
from dm.execute.run_select_influencer import get_influnecer_info_by_project, search_influencer_info, get_influnecer_user_id_by_project
from dm.prepare import get_dm_source, get_influencer
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

def login(username,password):
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
    max_try_num_get_user = 5
    try_num_get_user = 0
    while True:
        try:
            access_key = "nTYC9RbjpV8axJ3I9OnKI9Z4QVu7hzrE"
            headers = {"x-access-key": access_key}
            params = {"id": user_id}
            response = requests.get(url="https://api.lamadava.com/v1/user/by/id", params=params, headers=headers)
            json_data = json.loads(response.text)
        except Exception as e:
            logger.error(f"user_id:{user_id}/error:{e}")
            raise e
        else:
            if json_data.get("exc_type") == "NoFreeAccounts":
                logger.info(f"json_data:{json_data}")
                try_num_get_user += 1
                continue
                # if try_num_get_user >= max_try_num_get_user:
                #     logger.error(f"user_id:{user_id}/error:{e}")
                #     raise NoFreeAccounts
                # else:
                #     logger.info(f"get_user_by_id 를 다시 반복합니다. {try_num_get_user}/{max_try_num_get_user}")
                #     continue

            if json_data.get("pk") is None:
                logger.error(f"user_id:{user_id}/{json_data}/error:NoUserIdException")
                raise NoUserIdException
            return json_data

def get_valid_user_ids(user_ids):
    try:
        user_ids = list(filter(lambda x: get_user_by_id(x), user_ids))
    except Exception as e:
        raise e
    else:
        return user_ids

def send_message(user_infos, text, next_account_info=None, project_name= None):

    max_account_retry_num= 2
    max_request_retry_num= 2
    request_retry_num = 0
    account_retry_num = 0

    ###next_account_info 가 없으면 계정을 가져오기 있으면 해당 계정을 사용한다.

    account_info = infinite_login(username=None, max_messages_per_day=max_messages_per_day, session_id=None) if next_account_info is None else next_account_info
    if account_info is None:
        raise AccountException


    user_ids = list(map(lambda x: int(x["userid"]), user_infos))
    logger.info(f"user_ids:{user_ids}")
    try:
        user_ids = get_valid_user_ids(user_ids)
    except Exception as e:
        raise e
    if len(user_ids) == 0:
        raise NotValidUserIds

    ###dummy
    user_ids = []
    user_ids.append(53913868020)
    logger.info(f"get_valid_user_ids:{user_ids}")

    while True:
        if account_retry_num >= max_account_retry_num:
            raise AccountRetryExcessException

        sessionid = account_info.get('graph_session')
        username = account_info.get('username')
        password = account_info.get('password')

        ##send message
        try:
            response = client.direct_send(text=text, user_ids=user_ids)
        except Exception as e:
            request_retry_num += 1
            ### request 가 max retry 를 초과했을 때 다른 아이디로 로그인 해준다. request_retry_num -> 0 , account_retry_num += 1
            if request_retry_num >= max_request_retry_num:
                logger.error(f"client error:{e}, retry login // account_retry_num :{account_retry_num}")
                request_retry_num = 0
                account_retry_num += 1
                account_info = infinite_login(username=None, max_messages_per_day=max_messages_per_day, session_id=None)
                continue
            logger.error(f"client error:{e}, retry request // request_retry_num :{request_retry_num}")
            continue

        ##dm 발송 실패
        if not isinstance(response, DirectMessage):
            request_retry_num += 1
            ### request 가 max retry 를 초과했을 때 다른 아이디로 로그인 해준다. request_retry_num -> 0 , account_retry_num += 1
            if request_retry_num >= max_request_retry_num:
                logger.error(f"client error:{response}, retry login // account_retry_num :{account_retry_num}")
                request_retry_num = 0
                account_retry_num += 1
                account_info = infinite_login(username=None, max_messages_per_day=max_messages_per_day, session_id=None)
                continue
            logger.error(f"client error:{response}, retry request // request_retry_num :{request_retry_num}")
            continue

        ###dm 발송 성공
        logger.info(f"디엠 발송 성공 username:{username} /password:{password}/ sessionid:{sessionid} -> user_info:{user_infos}")

        ###dm 발송량 +
        INSTA_ACCOUNT_OBJ.account_collection.update_one({"useraname": account_info["username"]},
                                                        {"$inc": {"usage.dm": 1}})
        account_info["usage"]["dm"] += len(user_ids)
        next_account_info = account_info if account_info["usage"]["dm"] < max_messages_per_day else None

        ###
        completed_target_influencer.push_influencer_completed(project_name=project_name, start_date=None,
                                                              influencer_completed=user_ids)
        return next_account_info


        #
        # try:
        #     json_data = json.loads(response.text)
        # except Exception as e:
        #     request_retry_num += 1
        #     ### request 가 max retry 를 초과했을 때 다른 아이디로 로그인 해준다. request_retry_num -> 0 , account_retry_num += 1
        #     if request_retry_num >= max_request_retry_num:
        #         logger.error(f"json loads error:{e}, retry login // account_retry_num :{account_retry_num}")
        #         request_retry_num = 0
        #         account_retry_num += 1
        #         account_info = infinite_login(username=None, max_messages_per_day=max_messages_per_day, session_id=None)
        #         continue
        #     logger.error(f"json loads error, retry request // request_retry_num :{request_retry_num}")
        #     continue
        #
        # if json_data:
        #     if "thread_id" not in json_data.keys():
        #         request_retry_num += 1
        #         ### request 가 max retry 를 초과했을 때 다른 아이디로 로그인 해준다. request_retry_num -> 0 , account_retry_num += 1
        #         if request_retry_num >= max_request_retry_num:
        #             logger.error(f"undefined error :{json_data}, retry login // account_retry_num :{account_retry_num}")
        #             request_retry_num = 0
        #             account_retry_num += 1
        #             account_info = infinite_login(username=None, max_messages_per_day=max_messages_per_day,
        #                                           session_id=None)
        #             continue
        #         logger.error(f"challenge_required, retry request // request_retry_num :{request_retry_num}")
        #         continue
        #
        # if "challenge_required" in response.text:
        #     request_retry_num += 1
        #     ### request 가 max retry 를 초과했을 때 다른 아이디로 로그인 해준다. request_retry_num -> 0 , account_retry_num += 1
        #     if request_retry_num >=max_request_retry_num:
        #         logger.error(f"challenge_required, retry login // account_retry_num :{account_retry_num}")
        #         request_retry_num = 0
        #         account_retry_num += 1
        #         account_info = infinite_login(username=None, max_messages_per_day=max_messages_per_day, session_id=None)
        #         continue
        #     logger.error(f"challenge_required, retry request // request_retry_num :{request_retry_num}")
        #     continue
        #
        # if "challenge_required" in response.text:
        #     request_retry_num += 1
        #     ### request 가 max retry 를 초과했을 때 다른 아이디로 로그인 해준다. request_retry_num -> 0 , account_retry_num += 1
        #     if request_retry_num >=max_request_retry_num:
        #         logger.error(f"challenge_required, retry login // account_retry_num :{account_retry_num}")
        #         request_retry_num = 0
        #         account_retry_num += 1
        #         account_info = infinite_login(username=None, max_messages_per_day=max_messages_per_day, session_id=None)
        #         continue
        #     logger.error(f"challenge_required, retry request // request_retry_num :{request_retry_num}")
        #     continue
        #
        # if "Bad gateway" in response.text:
        #     request_retry_num += 1
        #
        #     ### request 가 Max retry 를 초과했을 때 다른 아이디로 로그인 해준다. request_retry_num -> 0, account_retry_num += 1
        #     if request_retry_num >= max_request_retry_num:
        #         logger.error(f"Bad gateway,  retry login //account_retry_num :{account_retry_num}")
        #         request_retry_num = 0
        #         account_retry_num += 1
        #         account_info = infinite_login(username=None, max_messages_per_day=max_messages_per_day, session_id=None)
        #         continue
        #     logger.error(f"Bad gateway,  retry request //request_retry_num :{request_retry_num}")
        #     continue
        # if "item_ack" in response.text:
        #     request_retry_num += 1
        #
        #     ### request 가 Max retry 를 초과했을 때 다른 아이디로 로그인 해준다. request_retry_num -> 0, account_retry_num += 1
        #     if request_retry_num >= max_request_retry_num:
        #         logger.error(f"Bad gateway,  retry login //account_retry_num :{account_retry_num}")
        #         request_retry_num = 0
        #         account_retry_num += 1
        #         account_info = infinite_login(username=None, max_messages_per_day=max_messages_per_day, session_id=None)
        #         continue
        #     logger.error(f"Bad gateway,  retry request //request_retry_num :{request_retry_num}")
        #     continue
        #
        # if "item_ack" in response.text:
        #     request_retry_num += 1
        #
        #     ### request 가 Max retry 를 초과했을 때 다른 아이디로 로그인 해준다. request_retry_num -> 0, account_retry_num += 1
        #     if request_retry_num >= max_request_retry_num:
        #         logger.error(f"Bad gateway,  retry login //account_retry_num :{account_retry_num}")
        #         request_retry_num = 0
        #         account_retry_num += 1
        #         account_info = infinite_login(username=None, max_messages_per_day=max_messages_per_day, session_id=None)
        #         continue
        #     logger.error(f"Bad gateway,  retry request //request_retry_num :{request_retry_num}")
        #     continue
        #
        # ###dm 발송 성공
        #
        # logger.info(f"username:{username} /password:{password}/ sessionid:{sessionid} -> user_info:{user_infos} /response:{response.text}")
        #
        # INSTA_ACCOUNT_OBJ.account_collection.update_one({"useraname": account_info["username"]}, {"$inc": {"usage.dm": 1}})
        # account_info["usage"]["dm"] += len(user_ids)
        # next_account_info = account_info if account_info["usage"]["dm"] < max_messages_per_day else None
        # time.sleep(10)
        # return next_account_info

def get_user(skip, limit, search_filter, filename, ex_project, ex_username_list, exclude_word):

    ##제외할프로젝트 설정
    exclude_userid_list = []
    if ex_project:
        project_userid_list = get_influnecer_user_id_by_project(project_name=ex_project, only_userid=True)
        project_userid_list.extend(project_userid_list)

    if ex_username_list:
        exclude_userid_list.extend(ex_username_list)

    ##몇개 가져올지 설정

    target_username_list = search_influencer_info(skip=skip, limit=limit, search_filter=search_filter,only_username=False, filename=filename)
    if exclude_word is not None:
        target_username_list = list(filter(lambda x: exclude_word not in x["username"], target_username_list))
    target_username_list = list(map(lambda x: {"userid": int(x["userid"]) if "userid" in x.keys() else None, "username": x["username"] if "username" in x.keys() else None}, target_username_list))

    target_username_list = list(filter(lambda x: x is not None, target_username_list))
    return target_username_list


def run(total_user_infos_group, text, project_name=None):
    next_account_info = None
    while total_user_infos_group:
        ## user_infos_list 중 첫번째 리스트를 뽑아서 메세지 발송
        target_user_infos = total_user_infos_group.pop(0)
        logger.info(f"target_user_infos:{target_user_infos}")

        try:
            next_account_info = send_message(user_infos=target_user_infos, text=text, next_account_info=next_account_info, project_name=project_name)
        except Exception as e:
            if isinstance(e, AccountException):
                logger.error(f"error:{e}, type(e): {type(e)}")
                next_account_info = None
                continue
            if isinstance(e, (NotValidUserIds, NoUserIdException)):
                logger.error(f"error:{e}, type(e): {type(e)}")
            else:
                logger.error(f"error:{e}, type(e): {type(e)}")
                continue

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
    project = "chungdam_hair"

    ##파일이름
    filename = "chungdam_hair"

    ##제외할 단어 유저이름, 프로젝트 설정
    exclude_word, ex_project, ex_username_list = None, None, []

    ##타겟 해시태그 설정 해시태그 설정하지 않으면 프로젝트 이름이 default 로 들어감.
    # search_hashtag = ""
    search_hashtag = get_dm_source.get_source_hashtag(f"{project}.txt")
    text = get_dm_source.get_source_message(f"{project}.txt")
    ##몇개 가져올지
    skip, limit = 0, 1000

    ##서치 필터
    user_followed_by_gte = 0
    user_followed_by_lte = 70000
    avg_like_gte = 0
    exclude_userid_list = []
    search_filter = {"$text": {"$search": search_hashtag, },
                     "user_followed_by": {"$gte": int(user_followed_by_gte), "$lte": int(user_followed_by_lte)},
                     "avg_like": {"$gte": int(avg_like_gte)}, "userid": {"$nin": exclude_userid_list}}
    ##1. 유저 리스트 추출
    user_infos_list = get_user(skip=skip, limit=limit,  search_filter=search_filter,filename=filename, ex_project= ex_project, ex_username_list=ex_username_list, exclude_word=exclude_word)

    ##2. 유저 분할
    total_user_infos_group = divide_user_infos_list(user_infos_list,  group_size=1)

    ##3. db 발송
    run(total_user_infos_group, text, project_name=project)

