# -*- coding: utf-8 -*-

import json
import math
import sys
import requests
import time

from dm.engine.user import user_split
from instagrapi import Client
from instagrapi.types import User
import logging
from instagrapi.types import DirectMessage
from instagrapi.exceptions import UserNotFound, ClientForbiddenError, ClientError
from db import m_instagram
from dm.engine import completed_target_influencer
from dm.engine.exceptions import *
from dm.execute.run_select_influencer import get_influnecer_info_by_project, search_influencer_info, \
    get_influnecer_user_id_by_project
from dm.prepare import get_dm_source, get_influencer

FORMAT = '%(module)s.%(funcName)s - %(message)s - %(levelname)s - %(asctime)s %(lineno)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)
if logger.hasHandlers():
    # Logger is already configured, remove all handlers
    logger.handlers = []
logger.setLevel(logging.INFO)

# host, port, proxy_username, proxy_password = "mobile.ipb.cloud", "7777", "customer-fydh21628401-asn-20057-sessid-RcPU-sesstime-1", "awR4Sad2t"
host, port, proxy_username, proxy_password = "resi3.ipb.cloud", "9000", "MrIlCvzYImHc0I3t", "wifi;us;;;;"
# host, port, proxy_username, proxy_password = "resi3.ipb.cloud", "9000", "AX7S3xZk5L9RF1So", "wifi;us;;;;"
proxy = f"http://{proxy_username}:{proxy_password}@{host}:{port}"

db_conn = m_instagram.InstaDB().conn
SERVICE_INSTAGRAM = m_instagram.InstaDB(db_name="service_instagram").db
INSTA_ACCOUNT_OBJ = m_instagram.InstaAccount(channel_name="instagram")
INSTA_ACCOUNT_OBJ.client_name = "admin_test"
USER_CHECKPOINT = SERVICE_INSTAGRAM["user_checkpoint"]
ITEM_USER_COLLECTION = SERVICE_INSTAGRAM["user"]
PROXY_COLLECTION = SERVICE_INSTAGRAM["proxy"]

max_login_try_num = 2
max_messages_per_day = 100
max_group_size = 30
client = Client()
client.set_proxy(dsn=proxy)
check_valid_user = True

def select_user(username=None, client_name=None, max_messages_per_day=None):
    account_setting_info = INSTA_ACCOUNT_OBJ.select_and_update_user(username=None, client_name=None)
    if account_setting_info is None:
        logger.info("no account available")
        return None
    else:
        logger.info(f"account is selected:{account_setting_info['username']}/{account_setting_info['password']}")
        return account_setting_info

#
# def login_by_session(session_id, username=None, password=None):
#     pass
#     # access_key = "nTYC9RbjpV8axJ3I9OnKI9Z4QVu7hzrE"
#     # headers = {"x-access-key": access_key}
#     # data = {"sessionid": session_id}
#     # url = "https://api.lamadava.com/s1/auth/login/by/sessionid"
#     # response = requests.post(url=url, data=data, headers=headers)
#     # data = json.loads(response.text)
#     # try_num = 0
#     # while True:
#     #     if try_num >=5:
#     #         return None
#     #     if type(data) is not str:
#     #         print(data)
#     #         logger.error(f"session return error - username:{username}/password:{password}, session_id:{session_id}")
#     #         try_num += 1
#     #         continue
#     #     logger.info(f"session return success - username:{username}/password:{password}, session_id:{session_id}")
#     #     return response

def login_by_sessionid(sessionid):
    try_num = 0
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

def login(username, password, sessionid = None):
    try_num = 0
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

def get_user_id_by_username_rapid_api(username):
    max_try_num_get_user = 5
    try_num_get_user = 0

    while True:
        if try_num_get_user > max_try_num_get_user:
            logger.warning(f"RapidApiError")
            raise RapidApiError
        try:

            url = "https://instagram-scraper-2022.p.rapidapi.com/ig/web_profile_info/"

            querystring = {"user": username}

            headers = {
                "X-RapidAPI-Key": "49247615ccmshcd5a0d0e8ddb542p1ae266jsnb64d93ff541c",
                "X-RapidAPI-Host": "instagram-scraper-2022.p.rapidapi.com"
            }
            response = requests.request("GET", url, headers=headers, params=querystring)
            # params = {"username": username, "access_key": "nTYC9RbjpV8axJ3I9OnKI9Z4QVu7hzrE"}
            # response = requests.get(url="https://api.lamadava.com/a1/user", params=params)
            json_data= json.loads(response.text)
        except Exception as e:
            logger.warning(f"user_id:{username}/error:{e}")
            try_num_get_user += 1
            continue
        else:
            if json_data.get("data") is None:
                logger.warning(f"username:{username}/error:{json_data}")
                try_num_get_user += 1
                continue
            else:
                id = json_data["data"]["user"]["id"]
                return id

def infinite_login(username, max_messages_per_day, client_name=None, session_id=None):
    while True:
        ##1. 사용할 계정 DB 에서 가져오기
        account_setting_info = select_user(username=None, client_name=client_name, max_messages_per_day=max_messages_per_day)

        if account_setting_info is None:
            logger.error("사용가능한 계정이 없습니다 infinite login 을 종료합니다.")
            raise AccountException

        ##2. 가져온 계정으로 로그인 시도. session 받아오기
        if session_id:
            login_session = login_by_sessionid(session_id)
        else:
            login_session = login(account_setting_info["username"], account_setting_info["password"])


        ##2.1 가져온 계정으로 로그인이 성공한 경우 받아온 session을 return 해준다
        if login_session:
            account_setting_info.update(graph_session=client.sessionid)
            return account_setting_info

        ##2.2 가져온 계정으로 로그인이 실패한 경우 계정을 새로 가져온다.
        else:
            continue


def get_user_by_id_lamadava(user_id, check_valid_user=check_valid_user):
    max_try_num_get_user = 5
    try_num_get_user = 0

    while True:
        if try_num_get_user > max_try_num_get_user:
            logger.warning(f"LamadavaServerError")
            raise LamadavaServerError

        try:
            access_key = "nTYC9RbjpV8axJ3I9OnKI9Z4QVu7hzrE"
            headers = {"x-access-key": access_key}
            params = {"id": user_id}
            response = requests.get(url="https://api.lamadava.com/v1/user/by/id", params=params, headers=headers)
            json_data = json.loads(response.text)
        except Exception as e:
            logger.warning(f"user_id:{user_id}/error:{e}")
            try_num_get_user += 1
            continue
        else:
            exc_type = json_data.get("exc_type")
            if exc_type == "NoFreeAccounts":
                try_num_get_user += 1
                logger.warning(f"json_data:{json_data} retry-{try_num_get_user}/{max_try_num_get_user}")
                continue

            if exc_type == "InstagramServerError":
                try_num_get_user += 1
                logger.warning(f"json_data:{json_data} retry-{try_num_get_user}/{max_try_num_get_user}")
                continue

            if exc_type == "UserNotFound":
                logger.warning(f"존재하지 않는 userid")
                raise NoUserIdException

            if json_data.get("pk") is None:
                logger.error(f"user_id:{user_id}/{json_data}")
                try_num_get_user += 1
                continue
            ###response type check(User Validation)
            else:
                try:
                    User(**json_data)
                except Exception as e:
                    logger.warning(f"json_data:{json_data}/{e} retry-{try_num_get_user}/{max_try_num_get_user}")
                    try_num_get_user += 1
                    continue

            return json_data


def get_user_by_id_gpi(userid):
    client = Client()
    client.set_proxy(dsn=proxy)

    try:
        response = client.user_info_v1(user_id=userid)
        userid = response.pk
    except Exception as e:
        if e.__class__.__name__ == UserNotFound.__name__:
            raise e
        elif e.__class__.__name__ == ClientError.__name__:
            response = get_user_by_id_lamadava(userid)
            userid = response.get("pk")

    return int(userid)

def get_user_id_by_db(username):
    doc = USER_CHECKPOINT.find_one({"username": username})
    return doc["userid"]

def get_valid_user_ids(user_ids):
    valid_user_ids = []
    for user_id in user_ids:
        try:
            valid_user_id = get_user_by_id_gpi(user_id)
        except Exception as e:
            logger.warning(f"{e}//user_id-{user_id} is not valid_user_id,{e.__class__.__name__}")
            if e.__class__.__name__ == UserNotFound.__name__:
                ITEM_USER_COLLECTION.delete_many(filter={"$or": [{"pk": str(user_id)}, {"pk": int(user_id)}]})
                USER_CHECKPOINT.delete_many(filter={"$or": [{"userid": str(user_id)}, {"userid": int(user_id)}]})
            continue
        else:
            valid_user_ids.append(valid_user_id)
    # user_ids = list(filter(lambda x: get_user_by_id_lamadava(x), user_ids))
    # user_ids = list(filter(lambda x: x is not None, user_ids))
    return valid_user_ids

def get_valid_user_ids_by_names(user_name_list):
    valid_user_ids = []
    for username in user_name_list:
        try:
            # user_id = get_user_id_by_db(username)
            # valid_user_id = get_user_by_id_gpi(user_id)
            valid_user_id = get_user_id_by_username_rapid_api(username)

        except Exception as e:
            logger.warning(f"{e}//user_id-{username} is not valid_username,{e.__class__.__name__}")
            if e.__class__.__name__ == UserNotFound.__name__:
                ITEM_USER_COLLECTION.delete_many(filter={"$or": [{"username": str(username)}]})
                USER_CHECKPOINT.delete_many(filter={"$or": [{"username": str(username)}]})
            continue
        else:
            valid_user_ids.append(valid_user_id)
    # user_ids = list(filter(lambda x: get_user_by_id_lamadava(x), user_ids))
    # user_ids = list(filter(lambda x: x is not None, user_ids))
    return valid_user_ids


def send_message(user_infos, text, next_account_info=None, project_name=None):
    max_account_retry_num = 2
    max_request_retry_num = 2
    request_retry_num = 0
    account_retry_num = 0

    ###next_account_info 가 없으면 계정을 가져오기 있으면 해당 계정을 사용한다.
    logger.info(next_account_info)
    account_info = infinite_login(username=None, max_messages_per_day=max_messages_per_day, client_name=None,
                                  session_id=None) if next_account_info is None else next_account_info

    # try:
    #     account_info = infinite_login(username=None, max_messages_per_day=max_messages_per_day, session_id=None) if next_account_info is None else next_account_info
    # except Exception as e:
    #     logger.warning(f"사용가능한 계정이 없습니다. 메세지 발송을 종료합니다:{e.__class__.__name__}")
    #     account_info = None
    #
    # logger.info(f"account_info:{account_info}")
    # if account_info is None:
    #     logger.warning(f"사용가능한 계정이 없습니다. 메세지 발송을 종료합니다")
    #     raise AccountException


    user_ids = get_valid_user_ids_by_names(user_name_list=user_infos)
    if len(user_ids) == 0:
        logger.error(f"len(user_ids)==0//{user_ids}")
        return account_info

    ###dummy
    # user_ids = []
    # user_ids.append(33873703194)

    logger.info(f"get_valid_user_names:{user_infos}/{user_ids}")
    while True:

        sessionid = account_info.get('graph_session')
        username = account_info.get('username')
        password = account_info.get('password')

        ##send message
        try:
            response = client.direct_send(text=text, user_ids=user_ids)
        except Exception as e:
            logger.error(f"response 에러:{e.__class__.__name__},{e}")

            request_retry_num += 1
            ### request 가 max retry 를 초과했을 때 다른 아이디로 로그인 해준다. request_retry_num -> 0 , account_retry_num += 1
            if request_retry_num >= max_request_retry_num:
                logger.error(f"client error:{e}, retry login //request 횟수 초과({request_retry_num}) 다른아이디로 로그인 해줍니다. // account_retry_num :{account_retry_num}")
                request_retry_num = 0
                account_retry_num += 1
                if account_retry_num >= max_account_retry_num:
                    raise AccountRetryExcessException
                account_info = infinite_login(username=None, max_messages_per_day=max_messages_per_day, session_id=None)
                continue
            logger.error(f"client error:{e}, retry request // request_retry_num :{request_retry_num}")
            continue

        ##dm 발송 실패
        try:
            DirectMessage(**response.dict())
        except Exception as e:
            logger.error(f"response 타입 에러:{e.__class__.__name__}")
            request_retry_num += 1
            ### request 가 max retry 를 초과했을 때 다른 아이디로 로그인 해준다. request_retry_num -> 0 , account_retry_num += 1
            if request_retry_num >= max_request_retry_num:
                logger.error(
                    f"client error:{e}, retry login //request 횟수 초과({request_retry_num}) 다른아이디로 로그인 해줍니다. // account_retry_num :{account_retry_num}")
                request_retry_num = 0
                account_retry_num += 1
                if account_retry_num >= max_account_retry_num:
                    raise AccountRetryExcessException
                account_info = infinite_login(username=None, max_messages_per_day=max_messages_per_day, session_id=None)
                continue

            logger.error(f"client error:{response}, retry request // request_retry_num :{request_retry_num}")
            continue

        ###dm 발송 성공

        logger.info(
            f"디엠 발송 성공 username:{username} /password:{password}/ sessionid:{sessionid} -> user_info:{user_infos}")

        ###dm 발송량 +
        # INSTA_ACCOUNT_OBJ.account_collection.update_one({"username": account_info["username"]},
        #                                                 {"$inc": {"usage.dm": 1}})
        account_info["usage"]["dm"] += len(user_ids)

        if account_info["usage"]["dm"] < max_messages_per_day:
            next_account_info = account_info
        else:
            INSTA_ACCOUNT_OBJ.account_collection.update_one({"username": account_info["username"]},
                                                            {"$set": {"status": "available"}})
            next_account_info = None

        ###
        completed_target_influencer.push_influencer_completed(project_name=project_name, start_date=project_start_date,
                                                              influencer_completed=user_ids)
        return next_account_info


def get_user(skip, limit, search_filter, filename, exclude_word):
    target_username_list = search_influencer_info(skip=skip, limit=limit, search_filter=search_filter,
                                                  only_username=False, filename=filename)
    if exclude_word is not None:
        target_username_list = list(filter(lambda x: exclude_word not in x["username"], target_username_list))
    target_username_list = list(map(lambda x: {"userid": int(x["userid"]) if "userid" in x.keys() else None,
                                               "username": x["username"] if "username" in x.keys() else None},
                                    target_username_list))

    target_username_list = list(filter(lambda x: x is not None, target_username_list))
    return target_username_list


def send_total_message(total_user_infos_group, text, project_name=None):
    next_account_info = None

    count_send_message = 0
    while True:
        logger.info(f"디엠 발송 시작")
        ## user_infos_list 중 첫번째 리스트를 뽑아서 메세지 발송
        if len(total_user_infos_group) == 0:
            logger.info(f"디엠 발송 완료")
            break

        if count_send_message != 0 and count_send_message%250==0:

            logger.info(f"쉽니다 5분")
            time.sleep(300)
            pass
        target_user_infos = total_user_infos_group.pop(0)
        logger.info(f"target_user_infos:{target_user_infos}")

        try:
            next_account_info = send_message(user_infos=target_user_infos, text=text,
                                             next_account_info=next_account_info, project_name=project_name)
            count_send_message+=1
        except Exception as e:
            count_send_message += 1
            if e.__class__.__name__ == AccountException.__name__:
                logger.error(f"{e.__class__.__name__}")
                logger.error(f"simal")
                return
            if e.__class__.__name__ == AccountRetryExcessException.__name__:
                logger.error(f"{e.__class__.__name__}")
                logger.error(f"sibul")
                next_account_info = None
                continue
            else:
                logger.error(f"error:{e}, type(e): {type(e)}")
                next_account_info = None
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
    project = "hclass_man_1"

    ##파일이름
    filename = "hclass_man"
    project_start_date = "2022-10-13"

    text = get_dm_source.get_source_message(f"{project}.txt")
    user_infos_list = user_split("""""")


    user_infos_list = ['lawyer_bmh', 'oneulee', 'minwook1231', 'viccc.ky', 'chazz__1218_law', 'un_peaceful_jian', '_jhhhhh93', 'ik__stagramm', 'rpsh41', 'ggobong3', 'three_kite', 'gijun2471', 'jack.jeong_law', 'imseong_lee', '1984san81', 'lawyeoul_lee', 'kxxhxjeong', 'dyenne_lee', 'onlyforilhae', 'tae.yyoung', 'lawyer_kimsy', 'eyyeonn', 'tresbien8', 'hufshadow', 'lawyer.sumi.lee', 'lawyer_kimhc', 'one_home_survive', 'mc_904', 'seyoon.j', 'cjsik5', 'lawyer723', 'ask_attorney79', 'lee.jongyop_4', 'hyu_legislation', 'sangu8879', 'hwhwkim_', 'hyunmok1024', 'fabian_chaebari', 'ikik0328', 'withyou3542', 'yul.ho', 'kocaesar1', 'beunsu', 'iamjhshin', 'scarletkyeong', 'jhpark_yujun_law', 'barexam.lawschool.co.kr', 'gounlaw', 'ena_eon_tori', 'sandersonia2015', 'i__am__k1', 'attorney_hong', 'pridegb', 'baek._aw', 'hyejeong6151', 'lawfirm_yulhwa', 'the_qwanny', 'juho.lee33', 'grassy_coffee', 'izzy_eun', 'sso.j.k', 'bomlawyer_', 'seunghunkim', '_zzmmin', 'iamahnvely', '211lawyer', 'yeon_junz', 'taylorkwon', 'genie_lawyer', 'lawfirm_damyoon', 'lily0804', 'lawer_lee_chungho_shitzu', 'hs_jh_he', 'law_elusive', 'y.j.boy', 'gunhuii_jo', 'nuy_know', 'christine.j.suk', 'mijin673', 'soseul_kim0104', 'lawyer_lim', 'lawyer_clee', 'cat_in_the_court', 'daejinlim_', 'yoooooojin313', 'ur79_lawyer', 'prime365dental', 'angelenoattorney', 'gostbtg', 'si_in_lawyer', 'nplawfirm', 'classiclawyer', 'jung12123', 'citizenlawfirm', 'doosik_jang', 'mylifelawyer', 'fitnessflo.pro', 'wook_law', 'smart_sanjae', 'fbqus', 'gmlawfirm_official', 'sera______law', 'myunghyun.no.1', 'artlaw.office', 'backenglish', 'lawfirmmsheo', 'dr_kyungsoo_kim_barun_law', 'stormplay5', 'lawsky_39', 'chung_yeonsuk', 'yulyul1130', 'redgreeno', 'geonho2290', 'law.how', 'wallboong', 'lawzeus92', 'titoinsan_lawfirm', 'lawlaw_landd', 'lawyer_kmk', '_jh_park__', 'donyounglee_lawyer', 'lawyer_mimi', 'law_jangwon', 'leeyujeong0919', 'lawvender_june', 'gamdong0311', 'kyoungran_2018', 'lux.lawyer', 'choi.s.j.lawbase', 'klac.or.kr', 'lawsteward', 'naeyillaw', 'hyeyoung_jeong', 'lawyer_imseunghee', 'shimji_law', 'lawyer_d.o', 'seo.jinyoung', 'jujaering', 'attorney_yoo', 'hunilc', 'dong_kune', 'namuneulbyeon', 'jerryp_ark', 'parkjonghyun8426', 'attorney_kyung', 'moonhyuck_kang', 'sol_daily_life', 'imosessye', 'sonlawmontv', 'soongin.law', 'yongbin7568', 'lawyerjiyoung', 'sagi__toon', 'april4moon', 'attorneyatlawseoul', 'romanticcrazy_attorney_kim', 'human2work', 'soyimlee', 'realtor_wdragon', 'shin10203', 'limkyungsook_official', 'patent4yougnjin', '_l9vely_', 'bo__ramiiiii', 'mdattorney', 'bbaczee', 'lawfirmhk', 'rayeon26', 'muse_se0', 'woopa1001', 'simp_lawj', 'sunshine.suji', 'bxx.lawyer', 'odd.lawyer', 'irvinebluesky', 'jongchaejung', 'gimsuhan2155', 'chaeseunglaw', 'hyejung.moon', 'brj_lawfirm', 'lawfirm_elite', 'boomolawyer2022', 'lawyer__mark', 'springmoonlight1', 'janghodangv', 'lawyerkohyejung', 'esol_law_office', 'woorihanalaw', 'puppysis2016', 'legalstaff', 'lawbin.kwon', 'jjang_0112', 'comfortlaw_pyg', 'within_law', 'hae_sung_h', 'shwoo78', 'gombyun', 'jhlawfirm_', 'attorney_jade', 'choiheekyeong', 'an.jinhak', 'attorney_kimjb', 'attorney_max', 'etranger_nasuyeon', 'moohyeop', 'lawntop_lawfirm', 'run.sangjun', 'lawyerparksangho', 'hyorin_mj_2', 'vilein_official', 'seodmlaw', 'g1_jung_', 'lkbnpartners_divorce', 'bs2nsibl2_', 'smile10hahaha', 'pyjlaw61', 'gupo_law_official', 'my.the.lawyer', 'hoonyhoon_k', 'sanha_ssultoon', '190814ajh', 'lawfirmkim', 'bbbang1213', 'taxtory5668', 'lawyer_colin.wh', 'ahnparklaw', 'bean.01.24', 'glory_ath', 'lawier3', 'hyojin_gwangju_lawyer', 'abogado3500', 'woorinee', 'bluewhiteclean', 'moonwon.esq', 'yoonpd_business', 'jamesjoonhak.ahn', 'lawvely12', 'lawfirm_law', 'lawfirmonk', 'jaewookhong', 'keemyungkwan', 'u_first_u1', 'lawoffice_ewha', 'lee.and.jeong', 'jss49300', 'lawschool__bear', 'kanggyun77', 'gwon_lawoffice', 'jpmo.ney', 'jjeongyun_in', 'cheon_jang', 'jungdamlaw', 'b.wsj0569', 'immanuel.sdg', 'alphacollection2904', 'nine_lawyer', 'chhlaw_shinsiljjang', 'law_jinjoo_yer', 'swleejin', 'jo_cjs_laa', 'ildansakorea', 'arch_0923', 'claire_plawyer', 'jiwon_9891', 'team_logos85', 'ydjlaw', 'park__lawyer', 'daeyeonlaw', 'attorney_oliver', 'lawfirm_baekha', 'leekwangduk', 'yhm_law', 'k_hyunsung_', 'nonomi1004', 'bitnacho', 'lawfirm.cnj', 'ilsanglaw', 'cpla_justice', 'suhan_joshua', 'miyako_lawyer', 'sarochoi', 'attorney_ra', 'yumyum_lawyer', 'gaby_min_jung', 'theveryjazzy', 'lawyer_jspark', 'siwol_ryu', 'seungeunlawyer', 'junhh.kim', 'elena.inseoul', 'jeong_yoon_choi', 'hanonelaw', 'c_u_in_court___', 'sincerely_eunhae', 'dals486', '2rin032', 'oseojin7', 'younq0405', 'dohun.kim.0', 'premium_lawyer', 'medi_law', 'lawfirmlee_n_kim', 'fourfree_flowers', 'louies_jk', 'lawyer_jylim', 'gwam2017', 'yklawfirm', 'tonycheong_74', 'yuujeong_h', 'chr1226411', 'dogamlaw', 'yujinshin313', 'jungyoun.lee', 'moonilhwan_lawyer', 'vita_hyewon', 'attorneytraveler', 'father.of.chamchi.samcheong', 'lawyer_ssong', 'attorneyh.hw', 'hopper_in_wonderland', 'jindongyeolbyeonhosa', 'lawfirm_miseong', 'lawtac.official', 'youngeun_817', 'hug_freiheit79', 'kimzisu', 'hansoolaw', 'lawfirm_leen', 'bryancho365', 'ming.g_kim', 'jylaw_', 'sangsokmate', 'ktkimlaw', 'lawin_with', 'eklee151', 'ssunssun91', 'gnoojnuyh_k', '_lawyer_yakbang_', 'daeyoo_daejeon', 'law_firm_jeongmoon', 'mj_cho34', 'law_centum', 'incheon_laywer', 'kim_lawyer', 'leekyungdeuk', 'isbn1237', 'lawyer_pil', 'solicitor_jung', 'wonu_chu', 'yhkimlaw20', 'jj.kim_attorney', 'hye5434', 'mi_ji724', 'ayko7984_law', 'our_lawyer', 'shinhyem27', 'kwon_standard', 'han_nwi_ho', 'malgeum_777', 'jinkim_neo', 'law3600b', 'siri_us_lawyer', 'snow_hjchoi', 'connectedh', 'jason_d.w.lee', 'ham_ik12', 'lawyer_parkjiae', 'rolex_06', 'l.d.h_lawyer', 'happyjt_lawyer', 'zb_law', 'bagjonghyeon83', 'lawfirmlim', '92su_jin', 'xvx_hyun', 'kimjh8318', 'dltngml222', 'cmw.im', 'maroosteno.choi.jj', 'kk01387', 'wehong530', 'yeohae_law', 'kimtaekkyun38', 'd.doug.kim', 'lawcchang', 'lee_kwang_won', 'kimne_lawyer', 'park_sun_beom', 'lawfirmgoodplan', 'laurepod', 'lawyerkdg', 'lawyer.taewoo', 'hancomtech_official', 'jeonghan_law', 'daehwan_crime', 'n.o.park', 'law_office_woonyul', 'seongmin_gang_', 'law_mingi', 'smilesman3', 'jeehaeshin', 'lawfirm_bupjo', 'chaeum179', 'adora.che', 'gyh6310', 'j___one2', 'dy_ska_', 'nochiavelli78', 'aini727', 'hj.rhee_bangbang', 'lawoffice_dk', 'mallaw_d', 'sijung_law', 'ishlaw_', 'farakicks', 'ososlawfirm', '_gphds_', 'leenpartners_lawfirm4', 'dawonee_1126', 'knj_lawfirm', 'lawyer_byeon', 'pokok211', 'younkulee', 'vroin_lawfirm', 'taeho.kim.4588', 'jhryu8306', 'hyeonjeong9963', 'smkim_seogyo', 'humornara_whitehouse', 'law_1mac_daily', 'law7hm', 'attorney_nsj', 'ks_lawyer', 'myoungjaeoffice', 'trademarks_d', 'lawyer_kmk_official', 'miny_9oo', 'seoyulcase', '20la2haru', 'jaesung.safelaw', 'haa_gogo', 'haeum._.hupat', 'lawyer_hskim', 'lawsmoh0415690331', 'suhwan__ha', 'eunja_rocky', 'lawfirmseoyul', 'bareungillawyers', 'law_rahm', 'open_lawyer_', 'elimlawoffice', 'onjolaw', 'attorney_yjkim', 'maeullaw', 'y2wings2', 'winy77777', 'hyang_hoon_kim', 'lawoffice_gongmyung', 'fencer.kim', 'heejin_seong', 'snap_sejong', 'attorney_minalee', 'hssoki', 'attorney_young_', 'lawyerysu', 'lawyer_yang_', 'tssmi3578', 'chul_park_attorney_at_law', 'lawyer_doodoong', 'low_hunmin', 'minji11201', '_go102', 'efsonada7', 'hakyoung_with_you', 'bewell_hyeonji', 'dami_leeee', 'sangsok119', 'sanwoolaw', 'sjyoolawyer', 'hsleetour', 'younjeonglaw', 'petlawyer', 'ghappypass.7', 'chanilaw8150', 'attorney_koh', 'sokbyun', 'lawyi_lawfirm', 'lovely_hanol', 'jeong_piljae', 'hyuck_bum_s', 'lawfirm_with', 'honeyneko', 'narinari215', 'yoonlaw1004', 'jeonik2021', '101lawfirm_official', 'ikchan_son', 'helaw1123', 'seodam_attorneykim', 'smiling.kim', 'jongdae.k', 'lawyer_checker', 'sooming9', 'lawfirm_tree', 'legit.law', 'yeji_5855', 'taelim2_lawfirm', 'jojihyeon506', 'ronne.feldt', 'arai_lawyer', 'kim_cho2n', 'dhshin84', 'lawtobe_', 'toboy91', 'youngtae_kang', 'physiostudio_2021', 'minheelee___', 'jslaw777', 'sukho_joo', 'youngbeeip', 'panki_kim', 'yksince2012', 'sohyuneeyam', 's.inhyeog', 'mocha_cream_latte', 'yj_law', 'dongwoon.oh.9', 'lawyer_leehyunju', 'banila27', 'yourside1021', 'jiyun_law', 'j_zcom_kr', '1994_lawfirm', 'lawkeeper_byunbyun', 'lawports', 'lawyer_ejlim', 'lnm_taxgroup', 'yoojialawyer', 'korealawfirm', 'zorba.kim', 'kijunlaw', '_csi_guidance', 'chongmyeong.jung', 'lawpark170', 'ibtlex9021', 'gc9lawyer', 'attorney_kyungsupark', 'bubdaelaw', 'raean_lawfirm', 'legalgroupdao', 'baek.law.diary', 'lawfirmshteam', 'lawfirmonnuri', 'nakkotsam_lawyer', 'guntorney___', 'together._.semu', 'rong______cho', 'lawyer_pbk', 'themorganlawgroup', 'yeoone_7', 'mini_mini.j', 'dearr.beauty', 'lawyer_jungsik', 'emfvks120', 'haju_lifenote', 'tax_hohye', 'kttttmj', 'dogfurtv', 'lawyer.on.the.desert', 'pangpang_one_', 'lawmkkim', 'seri_sh_kim', 'dlightlaw', 'nurse_law_', 'seokhoon0315', 'that_mains', 'namjk', 'outcourt', 'hoon_5_0', 'lawfirm.lawandpeople', 'kimgeuncheol83', 'park83man', 'lawyer_moon.is', '_luckylawyer', 'dooyu.law', 'jini_tax', 'jisuk.ihm', 'limsara_lawyer', 'gymseungchoi', 'law_office_sungyeon', 'rep.lawyer_jiyunpark', 'elenajeon', 'leelawyee', 'daesik_lawand', 'attorney_wook', 'ashlyn_eom', 'starlaw_official', 'rocohcom', 'maria_jhk', 'restaulaw', 'lykourgos__', 'villadelaw', 'rorodaddy_andy', 'coemira1012', 'hwy8238', 'hapoom26', 'junseok_90', 'law_ht', 'gamdong_law', 'ignition8407', 'ara_steno', 'lawyer_kimsehwan', '_mj_1st_t', 'visaplan_australia', 'lawfirm_seungwoon', 'heyb.design', 'shimji_note', 'attyhelory', 'travi_sw', 'lily_yoona', 'dani_law_0305', 'wktax', 'chsh0123', 'laborlawfirm_san', 'choeunlawyer', 'sunnam_gwangju_lawyer', 'happyhyunah', 'lawofficemj', 'j_y_yang_', 'lawposter1', 'maseong.lee', 'h.myung_', 'h_jung325', 'kyungheepkhani', 'gyuseok_jung', 'oh.gukjin', 'sonia_jang_', 'chlwus', 'thinkless_june', 'yoonhoo_clinic', 'seongeunhanyiweon', 'yeowoo.clinic', 'cozy3697', 'sungjun_lim9', 'jaynam122', 'imchae84', 'sim_beomsu', 'headfirst731', 'summer_kmd_poledancer', 'double__heat', 'kyungheeiq', 'yhshaniwon', 'kmd_hyeongtae', 'djjaseng', 'yjoo_ooo', 'chloe8635', 'xenhour', 'drinnylsh', '4everljy', 'khwwang', 'miall_km', 'jis_kiim', 'rinnnny_', 'xxavier_k', 'juyeoub', 'bcbctktk', 'hani_travle', 'hoe_cheon', 'callidesign04', 'jinhanbitch', 'allstar_jw', 'bora_eee', 'diagnosis_mj', 'heeyeonny', '___mong_kmd', 'first_molee', 'oh__myo__', 'rheejunwoo', 'medi.chef', 'aliceheeyoung', 'kmd_lej', 'angelslife14', 'yj_baek11', 'moyackh', 'onlysnu', 'jsyyyjsy', 'anssssseon', 'saengkiclinic', 'jaeseong3863', 'clairejmshin', 'onibtctu', '2roong_jang', 'myeongbeom.go', 'sh_clinic', 'dohwa_2', 'jongseung_park1006', 'coco____84', '_kweon', 'dg_jaseng', 'heejeong.oh', 'brmhaniwon', 'honeylee87', 'sams_tonggi', 'mrmrb092', 'dr.damien', 'shelter013', 'sanorico_fortuna', 'haeyulbusan', 'youngdaaaal', 'southkim0672', 'mind.healience.nyc', 'youngvbd', 'hjakamj', 'kyurimcj', 'ct_academy', 'iamjeremykim', 'gyuwoong', 'chonjaemeeh', 'jxhxyy', 'jdh_kr', 'allofhani', 'juji_1024', 'rekun123', 'jahyeonm', 'geummaek', 'myeonjuuu', 'jaemin8335', 'kmd_ril', 'sssangy__', 'jsw2333', 'tongin7257510', '_sieuniii_', 'korean_doctor_mj', '__kyu_kyu__', 'junseokandylee', 'hope.yo_', 'happy1839575', 'iy_h93', 'juangang1075', 'junyeongsong', 'dino_kmd', 'baejin.seung', 'seo_05', 'june_10.jun', 'ilzemae2', 'moonbeamer73', 'soo_e_15', 'praise7346', 'kingezv', 'geu_nyeong15', 'youngilmd', 'dearhani__', 'vvhope', 'kmspecialist_official', 'yoonks_93', 'gyulmedal', 'acu_thankyou', 'jun_broooow', 'leoncio_kim', 'kherb_official', 'jeonghoon_kmd', 'yujaehyeon3482', 'kdh1576', 'hankong2', 'th_terry', 'poey_eat_mik', 'sim.woonam', 'hyunseo_song', 'cy.__.lee', 'toovivid', 'seung_juice_92', 'chu_hongmin', 'nami_nini_jinam', 'hyeonjin.kim.165', 'jiyoo5578', 'baro_clinic', 'i_am_hyeongmin', 'sesang626', 'jooonnggg', 'ah.nuj', 'fishermen0506', 'm._jjun', 'yeongdonpyo', 'tkddbs4450', 'maang9', 'lsnghyuk', 'kmmh_center', 'askm_akom', 'min_2_407', 'dhwlgns_', 'do_khkm', 'jui_beoom', 'kwon_dkm', 'hyeunjong_you', 'talktalk_hani_', 'hoonji._.0127', 'mca2022cs', 's0ng_0_se0k', 'nvmdrt', 'seo.siljang', '6hm614', 'g_u2r', 'soon_june_', 'jooshin1', 'mc18336375', 'innbinnn', 'chamddle', 'youdam_clinic', 'sarrang0j', 'gloriality', 'ppazoo', 'bosin.h', 'mandoo_punch', 'h5_gun', 'jhyeoq', 'cleansam1075', 'p.i.m.p_lab', 'number1herb', 'dr.pista_chyo', 'dong_yuniverse', 'akom1004', 'bbaekkoya', 'cha.seunghun', 'hiong131', '_un_hyun', 'castle_zoo.97', 'choonghyun_han', 'qq0220', 'kjh._.9791', 'kmd_han_vite', 'min.uuuuu', 'lee.chae.hoon', 'aspeca_official', 'j.eonghui', '174cm.67kg', 'dongy_wookie', 'sstring_q', 'vlrmehd', 'bbin_610', 'all.in.an', 'dr.sharonguy', '_henri0215', 'sewon7960', 'junhwankim_md', 'sposdoc', 'seorry_thnkew', 'joo_holic', 'happeun_su__', '2h___ee', 'w_pooh_0125', 'yinny_wang', 'jjyong_ee22', 'kimhjsarah', 'dreampop0637', 'park_happiest', 'jae_hoo.n', 'minjungkey', 'yousunnnn', 'himnaera_her', 'jun._.ma', 'suyeonnie__', 'dr.choi_eyeclinic', 'eunbevey', 'haribo_goldbaren_official', '50rpc3', 'aerin_andrew', 'ahn_jaehoony', 'ispath95', 'kimjione23', '2big_zero', 'income_hun', 'choi_j2na', 'ysmed.lim', 'hr_donball', 'gkguswjd0', 'letsplay_jin', 'choi__luck', 'hamtorine1982', 'jinym2', 'emer_jincy', 'jiwoo_____1026', 'hako_yuna', 'whwodyddl', 'aarosa.a', 'kwun_kyoung_hyun', 'dofskim', '21stone_ps', 'kangsan0420', 'reamkee', 'gsign_kr', 'rsw0510', 'nearwind81', 'c.yoonje', 'daebagimom7', 'buchenwald17', 'thewellbeloved', 'hyunjincho___', 'juniuuuk', 'dr.jinwoosong', 'rob.st11', 'saidbae5s', 'hica_16', 'kujusa', 'hj_park_', 'dr.raouia', 'seongkyu_jang', 'feelardor', 'psy_cha', 'opndoctor', 'drjeonghankim', 'backtozero___', 'hyo_voca_tree', 'yourglory', 'yunjung.official', 'kkokkodak_', 'omelas_1', 'jogoon21', 'khoon93', 'colormom1', 'h.doyeong', 'cheongdambom', 'myoungje_song', 'kc_mint', 'dr_sojungkim', 'jooo814', 'jnwooi', 'twosuji', 'dr.leetaegeun', 'sunghyunu', 'ohyongggg', 'respiratorymonster', 'dots.daddy_of_two_sons', 'choco_zetty', 'jaerim_kim', 'yangheyjuuung', 'alse3025', 'ahha916', 'ehdghk24', 'goum22', 'sseoyunss', 'silentkorean_', 'gachonpremed_student', 'dr_needs', 'dr_yoohyun', 'joon_young_song', 'v_p.m_sodapop', 'd0heng9', 'de_faulty', 'bangjinhyeog18', 'fjrzl531', 'park_sanghyuk_01', 'acting_ljy', 'dentistyoungminpark', 'continue2me', 'esjh1019', 'dr_shinyskin', 'starry_hii9', 'pjennyyyy', 'kat_park_', 'ninccu', 'joonghy', 'yuha_kiiim', 'mihye_0301_', 'kelly__lee15', 'sherlock_hongs', 'xxiyehn', 'impact_hospital', 'kawaii_yoora', 'kj1905', 'dr._seonu_papa', 'seheehan715', 'terry_soohyun_kim', 'dalcom_320', 'andrew_lim817', 'rekun123', 'wndud8908', 'sarahki73', 'alexander.c.yoon', 'soo_b.2', 'iamjh526', 'ych.ch', 'jmin_00102', 'yohan.park.5036', 'mzet.j', 'bandabi_sangyoon', 'choiyuny0ung', 'bell_h.224', 'leadwhite01', 'seungseung_zzanggoo', 'yunnio.o', 'vanjini45', 'flawud_', 'nammers', 'somsome.woo', 'heart_conductor', 'tobedoc2020', 'brother_noon_', 'amazlngrace', 'silver_victory', 'medicaltv_official', 'kongdoc_kongdoc_', 'hongseon.lee.92', 'dr_anna_jo', 'ujin1727', 'mir_y.0513', 'yangkidoki', 'humanbyte', 'michellehan0708', 'chamed.official', 'coehyomi28', 'ssomday', 'sangmin2286', 'yaejikj', 'aloha_bboo__', 'hwaki_m', 'secondmountain57', 'mintclinic', 'drhonggiwoong', 'jan.3rd_02', 'okiwang97', 'appleks90', 'vein_master', 'kimdongsuk_dr', 'gumgum_e', 'hj__.kim', '_noble_rin', 'dr_kyong', 'sattvayogaseoul', 'janghyeona88', 'jihyeon.jung', 'sungjook1', 'lovelywitch', 'thegounskin', 'dr__taehyung', 'moonwon_', 'daedong2', 'drleejd_10', 'himym.story', '_tkyun', 'yuki.hiro.nana', 'songhansup', 'clean_ho_59', 'prof1t_is_zer0', 'onefivezero_', 'hy_lee1201', 'kwonmeans', 'choi_hunjin', 'kd__hyunn', 'toothfairy_2016', 'happy_ha_za', 'dr_jy_kim', 'sangwoo_115', 'yoonjung_95', 'dahyeson', 'ksm2221', 'dr.superdaddy', 'byungmo9', 'savior714', 'junhee4880', 'be_wannabe_', 'jackjung1998', 'mayblossom513', 'm.y_ice', 'hiyangbo', 'mo_onyaho', 'hajuneong', 'youth_dr.kang', 'doyoung_chung', 'js10081008', 'kkukudas', '_romify', 'forhappywomen_kr', 'joonhyeong.hong', 'kdkhiah_jack_ko', 'jungwoook_lee', 'altairys.create', 'humanpharm82', 'm.s._reminiscence', 'pr_team_mighty', 'k1020375930174', 'tem_alexshin', 'hhoon_lee', 'hyung_jin_choi_', '_yyeonvely', 'kiw_oong', 'bangjinhyeog9', 'gwoo_c', 'qod89', '3ane_mayov', 'jeff9.h', 'wallywooki', 'soooyerl', 'jeonginhwang9379', 'artinskin99', 'seongheumjeong', 'shinjjang_ns', 'davidontheway_', 'on_my_zephyr', 'junseokhu', 'dr.lovelykoo', 'ju_yeon0402', 'c.eurim_57_', 'j_y__p_', 'hluv__', 'c.s.w77', '20.long', 'lee_kyung_deok', 'yalli_yalla', 'sjlovemylife', 'lucamoons', 'mseonki', 'tkdkdkej', 'hxx.jxx', 'ryu3lim', 'je.oh.md', 'kjyeoni', 'charlene_ko', 'ck_seeyeon_official', 'jinseung_5_friends', 'sangah_woo', 'blackberet12', 'songkimsong0414', 'layla_0105', 'gemma_miso', 'hashleykim', 'yeonho0323', 'teamkh_redin9', 'kuheonnim', 'ricky_bae_3883', 'acmeci_official', 'ichon.forum.future.hope', 'jj_rad1418', 'sg.sugeun', 'dawon384', 'hji.an', 'seal_260', '__seong_je', 'sjpeterchoi', 'songyunyoung1', 'chrisjae85', 'yu._.jinee', 'rim.2.a', 'jseunoo', 'glad_ps_clinic', 'leonid_stagram', 'kang.minjo', 'kimkp908', 'shifting._.hwan', 'candle_ang', 'eight.ps', 'ddong_gunni', 'do.yeon_98', 'min.hee____', 'kdw9431', 'eun_sso0205', 'gyeom_byeol', 'hahm87', 'ccaccamury', 'd0kimmie0', 'han1595', 'choi_comee', 'hyohyo.87', 'joonchoipa', 'danielo_jinsu_kim', 'juhyuntak', 'goldhands.surgeon', 'hyungmini_818', 'allison_md.ped', 'heimish_jel', 'hyunsoo_zzi', 'june880203', 'hyuuukk', 'wxdn__', 'youngsun1462', 'suiljung', 'macs_bong', 'winfordace_15hoytyd5', 'kimmsnim', 'unasyn', 'sameowa', 'dohy.00', 'y_u__z_u', 'j_xincere', 'nongphuonganhtopcos', 'leemanwoo5', 'yimvely92', 'yoon.s.w', 'noela_2020', 'byoungwookcho', 'sanghwan0522', 'clahhic', 'wmh7800', 'aveingers_tv', 'haewonism', 'doctor_fmharu', 'p_orange415', 'rickero', 'u_dol2vv', 'womanspring2016', 'taeyang.choi.9', 'penilee88', 'cqcqthisisw9gfo', 'ssyeonn__', 'jangwoo.kim', 'angela4sunny', 'haroop_design', 'kimsohmin', 'sanghak45', 'pushing_root141', 'taeseong.jung', '0_tjflrkdmf_3', 'ehdgusl2', 'newbietotheworld', 'summacum_laudexx', 'mingyong777', 'tedryu2004', 'bellacastro147', 'transcendent20', 'h_ae_gin', 'hzlee91', 'jiteun.text', '4086rahma', 'bollymollly', 'ssomver_kr_bonitobody', 'cosyahn', '715sm', 'ijongweon491', 'mm.ung', 'apnalchangchangjeondaryeon', 'oh_mg7825', '2ee_jaehun', 'la.ssong', 'kimmisun23', 'hyeonjeongsil8', '20022628k', 'hj_fvb', 'pulse_ho', 'eui_momo', 'dal.xoon', 'goldenpick77', 'jhwoo1012', 'my_story_and', 'hye_juice__', 'ins___official', 'juns_4066', 'eylu.l1912', 'ersta15', 'id0ntkn0w8705', 'dongpillcho', 'andialso_stone_joa', 'f__uuunu', 'strawberryjuiceey', 'johyiseong243', 'lee_hs_01', 'hy.e_e.yh', 'hy__nseo_', 'truth_seeker_sb_', 'bro_w_', 'idongmyeong80', 'jhkimeye', 'minsung118', 'i._.revlis', 'kaivrary_stud10', 'go_oooonie', 'studying_kj', 'soccerstory_w_fc', 'sungjoe.bae', '_alicechoi', 'coollifeis3386', 'zoomoutinout', 'cxdxdex', 'onyoure____un', 'janepark08', 'design.oda_official', 'thequad_shop', 'medi_coach', 'oas27752', 'ddoch10932', 'whitebear_nurse', 'chadoctor5', 'bobos.golf', 'coolkyj', 'oyuul_clinic', 'lawyerwsc', 'haej1_.y', 'readingjeannie', 'yangjuuuu', '_tsg_10', 'bientrans', 'masta.lee.12', 'what.__.iam', 'hongdaekim_', 'hulampro_official', '2u._.nen', 'dorazi98', 'cozy_syg', 'sangchies', 'childhosp_seoul', 'yoyoyosiyosiii', 'hijisu_u', 'dla0701', 'si._.aaaaa', 'ppkii1', 'avokado_jung', 'clinikaiv', 'xicexbearx', 'mippeum_clinic', 'wonderbox_pub', 'kaleighcharlize150', 'momamene', 'lyg._.98', 'gilpia0818', 'meoinstein', 'ssol._.loz2', 'tember_winter', 'i.m.hyesol', 'sea.jjang', 'hyeri.songg', 'kindokang', 'wony235', 'rokmc1098', '_kangheeyoo_', 'nobility_cp', 'thankyou_company', 'daun8088', 'jcivalier', 'sinu__u', 'webceph', 'jslee806', 'dohwan8191', 'skyier5', 'flexpinebrace', 'gk_hwan', 'youngsoosoh', 'orchestra._.kim', 'sus_annahn', 'kakakakakaa2817', 'babychavha__', 'i_luv_iiit', 'v1.lab_official', 'namchoolkee7', 'zin.ri_', 'dan.danu', 'juheeran3', '_keep__ros2y', 'jeeeun.lee.520', 'enitour33', 'youfit.khu', 'eagy_detox', 'plumm_d', 'stakato27', 'jisooo9620', 'abigail_sinjae', 'sane_7_sane', 'his_dormitory', 'munji_han', 'hyoniiiji', '_n_n_rin', 'allday_beautii', 'cmg_3dxr', 'josubin_official', 'iseunggi5161', 'liu_mei_clinic', 'jayzero_', 'woongdoctor', 'osm1253', 'sea_river_water_life', 'ma_young_min', 'kim83daddy', 'kihuni_kim', 'ditto_media', 'ggo_ong__97', 'febryj', 'hass_hoon1', 'choigyudong2', 'gangbyeongguhyeongnim', 'tears1288', 'kongchilovegomdolstardochigum', 'cherrybori_jungmin', 'ahyunia', 'b_humble_ego', 'cartes_kimds', 'hogjmjae', 'xxkm_choixx', 'keunhospital', 'choi14854', 'hangl_ch_j', 'hbreigina', 'dna1246', 'meganekunk', 'yoeonshin', 'jua.__.na', 'rrnxvn', 'sangjune.lee.33', 'ardunge', '_wisojen5', 'path._.u', 'hmhansol', 'junghyunsub27', 'ilovemsl', 'yeonu.choi', 'upstagram69', 'faith_dy.kim88', 'wohwgiav', 'kimwon_b', 'one_ca5563', 'webceph_s', '5type.leveragesystem', 'westsunone', 'zydechoz', 'jo_mame', 'green_hearing', 'specialist.ck', 'jja6899_', 'art_vaccine_cafe', 'seunghyechuuu', 'johyejeong3832', 'serranodarriulat', 'y0ung_h00n', 'eelnooyah', 'josh.busan_southkorea', 'ghq_86', 'ysoo9712', 'leeyeuni.t', 'cu.yuae', 'sandy.ghill', 'jeegeon_00', 'syc6204', 'bana.nawa', 'ojay0', 'writer_hyosue', 'korea_kid_05', 'fyisr_8', 'beginner2018', 'sj_beautygallery', 'ssong._.yejin', 'egg._.zer0', 'jenny_luvz', 'jinniesuh2', 'luvluvluv1112', 'jiwankwak', 'code_maetamong', 'jk97113', 'booklubeedubee', 'juwon_seo_94', 'sungjoon.cho.127', 'zeliard1', 'zoozane10022', 'dh_shin97', 'jjjj1111114', 'gosan__os', 'cosmos_1477', 'godlfldmensm', 'y.lee.dpfla', 'kaphd_official', 'seong0jang', 'kimju1657', 'dr.veronica_chang', 'soommeditech', 'woojoons', 'white_night_closet', 'rlo.water_', 'arc.dpri', 'maengjinyeong9', 'kjho011', 'anonym5753', '94__heeee1', 'seeyoung87', '_sh_5o18', 'snum_h_j', 'seungtaeg11', 'momo.jnxx', 'airysteps', '93.sh.yoon', 'jjin.1229', 'lee.doc1', 'rubi_co_1810', 'joseph_h.t.hong', 'juhyun010318', 'dsdaedoo', 'tongcle_official', 'kyung_h_36', 'connectedu2017', 'cha.seunghun', 'dubiel2005', 'jjh_9595', 'yujin_n2', 'lifeartist_marketer', 'agape._.agape', 'aepion_company', 'yoon.joseph', '2duck0', '_radiant_abcd', 'taeju97', 'tmlkorea', 'u17470', 'angelwheesung', '_kimgyujin', 'tobongggg', 'bluewhale_134340', 'choi._ubin', 'ya_poooooo', 'ye._.o98', 'musicophilia_2hm', 'v_victory_of_s2']

    ##2. 유저 분할
    total_user_infos_group = divide_user_infos_list(user_infos_list, group_size=1)

    ##3. db 발송
    send_total_message(total_user_infos_group, text, project_name=project)
