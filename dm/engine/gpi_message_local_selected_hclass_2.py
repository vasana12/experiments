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
# host, port, proxy_username, proxy_password = "resi3.ipb.cloud", "9000", "MrIlCvzYImHc0I3t", "wifi;us;;;;"
host, port, proxy_username, proxy_password = "resi3.ipb.cloud", "9000", "AX7S3xZk5L9RF1So", "wifi;us;;;;"
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
    project = "hclass_man_2"

    ##파일이름
    filename = "hclass_man"
    project_start_date = "2022-10-13"

    text = get_dm_source.get_source_message(f"{project}.txt")
    user_infos_list = user_split("""""")
    user_infos_list = ['lawrin13th', 'lawyer_cham3', 'seheon_law', 'lawyer_knr', '2jongki2', 'iss0083', 'kim.sun.kyun', 'kangsan0329', 'omgjunhyuk', 'limav23170', 'spiritblue7', 'lawyer_oh_', 'fi_cher', 'jiyoon_baik', 'kwanki.kim.1', 'heebongha', 'betterbrady', 'on.ssong', 'yeoborami', 'sangoh.park.law', 'psj6553', 'im_mijung_80', 'cafentrip', 'coco_sy___', 'saayyy__', 'l_juseok', 'lawyer_lena_ha', 'yunsik20', 'yoonsokgi_', 'kang_chul', 'demian_lawyer', 'saeonyul', 'lifegoeson36', 'lemon19s', 'suminyin_nim', 'junkim9525', 'byeblue13', 'kyrie_kyrie_eleison', 'lawmb7', 'sbspcman', 'lawoffice_haeju', 'a.r_yun', 'kim_hyoung_uk', 'heysummer_official', 'wish.done', 'lj.kr', 'blessbyun', 'koreadca', 'madcow_9715', 'humble2myself', 'bk.moonn', 'lawyer_jkm', 'jeongcomet', 'ahnpark_park', 'breathe__in__', 'minsisterfam', 'kinggodhyunghwa', 'lawyer_hyt', 'kwanghwe', 'ebslawyer', 'jamaica_a', 'leggo_law.school', 'inhwa_paik_88', 'law_sal', 'todaydaeun', 'wasabi.kitchen', 'lawyer7andre', 'jaycho407', 'msangy_3', 'hj_law85', 'micky.pej', 'space._collection', 'jskim_03', 'freeharassment', 'wonder_lawyer', 'moaklawyer', 'starry_shim', '_eat_daily_', 'gom_dory', 'hanseon_3', 'kwang.min.park', 'lee_yongho_at', 'jihyanglaw', 'rullu____ralla', '_n_n_rin', 'lawyer_ej', 'youngthousand7', 'dia0909', 'namyangju_lawyer', 'jh___choi__lawyer', 'lawyer_kim.js', 'attorneyhannah', 'mung3nyang3', 'busanbar', 'jobyun_daily', 'm.a._.lee', 'welchom12', '1983_mini', 'attorney.jhhan', 'seo_hyunny', 'choijisu643', 'jeonhyeonju700', 'jeyeon1228', 'kay____h', 'minjungeeh', 'ihave7idea', 'lnpartners_law', 'kkyung92', 'jaeyunlawyer', 'lilawga', 'gandigy77', 'jikimi0811', 'gaengsik_', 'synonym777', 'junlawyer', 'yoonwoo_______lee', 'life_of_cyan', 'joshua.roh', 'chaeji90', 'mountain_lawyer', 'munseaki', 'lawlovesong', 'namchul_chung', 'love_healena', 'bling_bk', 'nanbada_travel', 'miri_2017', 'hunjingun2', 'wolabae', 'iamminhee_summer', 'inchanabby', 'k_imvest', 'lawyerjun81', 'jay9990o', 'hanmctv_official', 'pikashine', 'jiyoon_lawoffice', 'geumcheon_lawyer', 'jonwoojung', 'ysluvr', 'sanguk_lee7', 'ksing333', 'minho_lawyer', 'lawcreator', 'hyunsoo_law', 'eun._.ha', 'bini4372', 'good__lawyers', 'lawfirmsowon', 'zieumlaw1155', 'goodpeople_law', 'tokung978', '2hondosa', '_kr_law_92', 'adminlaw_jung', 'jonghyuklee_lawyer', 'law_ryu2', 'misk510', 'dohyeon_222', 'h_moclano', 'cjy3345', 'kyoungminma', 'juliet_in_the_', 'olraengpia', 'yeonseoklaw', 'fenrir31.k', 'lawyer_seo', 'jjww8844', 'suji_833', 'lawfriend7985', 'pacific.american.univ', 'kim__jungwook__79', 'archilawyer_gym', 'sum_177on', 'eveglow2', 'byononsa', '2sangh5', 'law_n_star', 'bellearbellear', 'young.kim629', 'changjoonjang', 'parkjonghyun_lawyer', 'korea1percent', 'chae_i_sok', 'lawyer.minsung.kim', 'ju____heeee', 'lawfirmsoul', 'lawyer_chungman_choi', 'knslawyersoffice', 'park.jonghyun_', 'jeng_sijin_', 'byungchulkang', 'imlaw.co.kr', 'baek___js', 'jp_law_collector', 'tax_hys', 'head105m', 'songbyun_toon', 'visitlaw', 'lawyerbang22', 'bliss_s2022', 'lawfirm_thel', 'rinkimlawyer', 'freepeople71', 'cho_mihyun_lawyer', 'lee.hanui', 'seonyu_siu_papa', 'lawyer_park_eunhae', 'kim_and_partners', 'lawyer.ung', 'lawyer_sonjihyun', 'bblaw_official', 'junghwan9557', '2ndgrs', 'law____jlim', 'lawseon1', 'gwangseonlaw_official', 'lawyer_sonjiyoung', 'moon_eul', 'lawfirm_danbi', 'iseungjae2514', 'law_mjrhee', 'refillyong', 'ulsan.lawyer', 'fortitude99', 'sinclairoh', 'goldenlaw119', 'lawfirm_renaissance', 'lawyer1221', 'kyunginlawfirm', 'ryu_kijun.lawyer', 'minnie_jeongminlee', 'lawyer_heymin.k', 'seoghwa.i', 'minwon110', 'lee_jeongjoon', '_yoohnwa', '_law_pamine_', '_aegislawyer_', 'ynghynkim', 'jung__ah__k7', 'choi_jeon_law', 'lawyer.jdi', 'dbdbnew', 'justall011', 'lawyer_kimboseong', 'lawyer_kht', 'kyoungyhong', 'kch_lawyer', 'attorney_a.j', 'iskra0627', 'cofferfume', 'thefirmulaw', 'lawyer_kimsiwan', 'lawth_jjw', 'ohkims_ip', 'joojoojinjoo', 'tgs.cslaw', 'law0517', 'daewoonglaw_re', 'dojinsoolawyer', 'jylee.cpla', 'dongs_eung', 'lawofficesoho', 'yeojunglaw', 'lawsaengmon', '100_hanna', 'ssyy_kiim', '00luckypapa00', 'narilaw218', 'yooong6403', 'oh42194219', 'ahdkjshjdjkshj_14', 'bumsik77', 'usvisa_ollim', 'silvergirl9312', 'woonni_ahn', 'bang__hokeun', 'ryujaemin01', 'lawfirm_theday', '_shyelim', 'cplafriends', 'lawyer.hoon', 'khushi_sakhare12', 'ujin1312', 'jaeheon_law', 'glo.w.law', 'lawplus_', '2021lawyer', 'jangseonggyun38', 'navesky', 'chdlawfirm', 'jaelming', 'kwon_law', 'dasol1032', 'seoungillhan', 'imlaw_7', 'kimjihyun1101', 'chohyuntae9881', 'ji.always', 'yunandlee_', 'vroin_visionroadin', 'moon_younggon', 'lawyer.jeon', 'yeyunlawfirm', 'eunna____', 'wonwootae', 'chahyeunyoung', 'cheong_dam_rehap', 'hankyungtae81', 'justina_0626', 'lll_3l_lll', 'anlab_law', 'yunjung0918', 'lawfirm_mayday', 'minkyu_chung4237', 'mdlawaj', 'yuyeon_labor', 'lawyer_hwang', 'songyi.j', 'ceonjuhyeon1417', 'lawfirm_mirinee', 'lawyer_msj', 'takinkwon', 'qkrquswhgk', 'law__ing', 'gonggam_lawfirm', 'lawyer_kang_', 'hmlee.cta', 'eunssong_seo', 'plawyers_official', 'aran_minju_', 'centrolaw', 'k5stars75', 'kimkangeui', 'lawoffice_dream', 'kingsbini', 'gilhohan', 'lawfirm119', 'sejulaw_lawfirm', 'yong_tak_jun', 'lee_byun_mom', 'symoon224', 'boo.bnklaw', 'lawyerhhj', 'lojlon_eh', 'lawyer.hskim', 'saenggyehyeongbyeonhosa', 'law.yslee', 'woongjoo_jang', 'sungcheul.yun', 'attorney_eric_kim', 'lawyer_wp1320', 'hak_lawyer', 'bangsam22', 'myunggeun.shin', 'law_jimin', 'lawgical_haesol', '_moru210', 'with_yeyul', 'pnkpatent', 'maum4unet', 'dr_sangdari', 'saeol_law', '3uni_b0on1s', 'sjlaw03', 'hyungmyungkim', 'iamk.law', 'sm5410', 'limjy1006', 'gentle_lawyer', 'mina_jlaw', 'lawyerkwon', 'yoon6_film', 'rubysoyu', 'woorin.sung', 'yonghwank2', 'lawwinlaw', 'justice_crime', 'yunhyungsu', 'best_daeinlaw', 'lawfirm_victory', 'sklee_03', 'w._.gram', 'lawfirm_youlrim', 'lansunlawyer', 'parkyeji77', 'lawfirm_pk', 'lawyer.jy.lee', 'leejwoo1004', 'lawma_fit', 'jh_yplaw_cn', 'hyunho_jung9508126', 'lawyer_parkej', 'jwim0123', 'ko_seungwoo', 'lawyer_dg', 'woori_bomon', 'uan_lawfirm_seoul', 'starlaw_hm', 'damyullaw', 'cplahan', 'shine.d.h', 'lawfirm.jy', 'leo_pet_cat', 'yoon.attorney', 'miseon9301', 'lawyerkimdoyun', 'bluechairlounge', 'yaholaw', 'lawyer_bangjh', 'soyulawyer', 'promiselaws', 'garojelawfirm', 'seungwonlawfirm', 'good.attorney', 'themoments926', 'lawtimes_1950', 'k__ayoung', 'law_tl032', 'j.0915', 'suhbongha7', 'yoonbeaver', 'issholawyer', 'dhrryh', 'mingyoo_park', 'lawchoffice', 'brightsun_lawyer', 'daisukeinaba.com_lawyer', 'lawlawri', 'hanle791029', 'sattotv_official', 'andreahans', 'lawyer.jjmoon', 'uijeonglaw', 'ammm.bj', 'lawyerclick', 'sungsin.kang', 'pacoism', 'daegun3800', 'micha_elaw', 'lawfirmhyean', 's_young_jjj', 'jsh1561', 'goodneighbor_law', 'meltingpointv', 'kimmusa_jonggoo', 'vyongvyong', 'leekw.36', 'shinseonguk1977', 'hajeongmi2', 'choi.kiuk', 'soulsis822', 'gyeyanglaw', 'r12032019', 'lawyer_sri', 'lawyer_ohjungsik', 'mindory_helen', 'jhp_lawyer', 'jennyes_s', 'jijootaek_lawyer', 'lawyer.wslee', 'laforet_store', 'lawasis_firm', 'slchan_b', 'ibslawyer', 'jch_kim', 'lawyer_hwang1', 'kang_sang_kuk', 'haerang_law', 'kbs087103', 'seoha_laborlaw', 'lawhill_korea', 'gajin_bae', 'lucete_sooyng', 'compact_bar.review', 'sungho8780', 'starlawfirm_official', 'saccofillas.korean', 'leehwanglaw', 'theall._.lawoffice', 'jinhee_jeon0', 'debtlawyer_', 'ssso_oc', 'lawyer_cc', 'suojae_hj.kwon', 'seonryul1', 'lawfirm_kwonhan', 'lawfirmsolon', 'baenyun_kim', 'law_sbk', 'thessen_patent', 'hj.kwon_m', 'attorney_cho', 'bsslawyer1', 'dootoom_law', 'bettercall8282', 'okogenki', 'eivarnelt', 'myungsook.jo', 'toon_law', 'lawyer_habyeon', 'joon_woo113', 'thkimed', 'my_yunbyun', 'jucp1', 'law_gyeol', 'junkyu_nam', 'white_lawyers', 'syonggeol', 'yeseom.lee', 'majina2020', 'choijun.design', 'study_law_again', 'shoedoc_official', 'cpla_0916', 'hanqkim74', 'reviva_and_spring', 'lawyerjkim', 'ssongbeon', 'ahh119pasan', 'howtalk.co.kr', 'diathenalaw', 'hacked1836251638', 'suilaw', 'parkmunilawfirm', 'min_24hour', 'eunboy', 'ahn.j.b', 'yegaro1721', 'delig_ht_', 'lawyeryuna', 'pji7672', 'hayoonkane', 'star_muk.s', 'sunsong2121', 'sungyong.m', '21csolomon', 'jooan_park', 'jeongsuho1984', 'yiji_rim', 'sagun_law', 'lawyerkyu', 'north_attorney', 'your_academy_english', 'h.onestone', 'siru_style', 'hongsokgi', 'luv_lawwire', 'psj_lawyer', 'dowon.official', 'law_ryu', 'ramilawoffice', 'dj1law', '5east2', 'urmasterpieceofgod', 'mpman2900', 'udonkim_jigeum', 'ohyun_phillip', 'nexilis_sj', 'jwkim2016', 'seoulviewclinic', 'bsjongtae', 'seoingyo_lawyer', 'tae._ri_', 'haeyultime', 'jaeseong.lee.7543', 'parklawyer', 'lawmajor2002', 'anlablaw', 'yeonki81', 'hana.cpla', 'purergold0319056481', 'letsgiri_', 'leeminui_lawyer', 'hajw2019', 'lawyer_leehyunju_', 'ayk_lawsd', 'lawfirmchangchun', 'gosohage.official', 'lawyerchoe', 'leehana_21_', 'jeiahmee', 'ussle_lawanna', 'hansol.lim.31', 'hyungjoonhan', 'h_8.h_8', 'attorney_at_5', 'seo.cta', 'tong1.8253', 'yplaw.co.kr', 'sn_labor_life', 'junghc.law', 'lawyer_sooa', 'ohringe', 'hans_attorney', 'centumlaw', 'lawyer_khk', 'lawseonco', 'sekwang_students', 'jeguk1101', 'lib_law', 'veatlaw', 'lawyer_jinhyuk', 'angelababy0409', 'kim.byeon', 'lawfirmyeju', 'mindandlaw', 'gyunmoon', 'serimlawfirm', 'uijin_hong', 'hwarang_lawyer', 'lawyunsun', 'law_1mac', 'bitt_law_official', 'lawyer_kjm', 'wook_nomusa', 'safelaw_justlaw', 'g1_sokgi', 'lawyer_an_gabchul', 'parksangho76', 'stars.and.themoon', 'stbfly101', '_daldalhada_', 'applewithcone043', 'yoursunlaw', 'lawyer_soondubu', 'myungga_lawfirm', 'leeinchul73', 'luv__hiri', 'seo_lawyer_', 'the_kim', 'yuuniyoon', 'lawfirm_yoohan', 'kingofloan', 'raep.law', 'alicia_yun', 'teheran_crime', 'jiyul_sokgi', 'kmhejn', 'dongjoopark_', 'law.lee.law', 'jkha_law', '__rawlaw__', 'my_law_year', 'ayelaw512', 'naajoong', 'feel_law', 'lawoffice1208', 'yousimlaw', 'dongholaw2022', 'lawfirmak', 'lawyer__lee', 'leeshiyune', 'taehyun_attorney', 'lawyerhc2020', 'elliot.yaeahn.park', 'legion_etranere', 'haiyaaan_n', 'lawyer_choijoonhyun', 'skybong4700', 'heongyu', 'lawofficech', '__jaeyeon___', 'hamji_lawfirm', 'law_office_bnk', 'law.wikitv', 'abogadodiazdavid', 'lawyer.yu', 'euno_lawf', 'donghwa_law', 'lawyer_dslee', 'presicho', 'ck.daddy', 'kohbruce.law', 'kangilmo', 'kyoungjong.roh', 'lawstory_official', 'skpsh41', 'lawyer_lhj', 'moont76', 'lawfirmyc', 'lawyer_koh', 'sulleelawfirmpllc', 'jylawoffice_', 'hanno.d.law', 'ckm_lawyer', 'hongnono1', 'in_hanpan', 'jjin_gu', 'gwonang', 'hanijyj', 'ryu_and_you', 'yongik_96', 'y_heek', 'manfit_kmd', 'downtothebottom', 'hungrigulv05', 'pau8l', 'drduck1126', 'jeongmin636', 'dd_brightening', 'hseok_yoon', 'lazzyhye_', 'saengkibundang', 'jeongyunseon5209', 'healing_8', 'jeong.jh1106', 'ho_ratio', 'dreambkmc', 'freehug_us', 'acuhan4', 'cozy_hongji', 'kdbherb', 'firsthidol', 'jung.won_hee', 'baemijo', 'petrichorjh', 'gm0113_ha', 'dreamhani2012', 'kjhun862', 'jinmin_luce', 'jabok.lee', 'ryu_jiyeony', 'be_wis', 'drzeuspark', 'meenj_', 'choehyojeong', 'shinchonshes', 'bubbly_bly_', 'leejeongmin9292', 'hunsung_', 'jeongwook.choi', 'lhbstart', 'psh_polarbear', 'jeonkibeom1990', 'aisarhpue', 'jayeonjaesaeng', 'younghee.seoul', '0_hwane2ee', 'pparkmani', '199.20.299.54', 'yeongsu1212', 'romantickmc', 'formidable1', 'joaaana.kim', 'hyunjin_2222', 'hyeganghani', 'jhhan_81', 'davidoh_1227', 'drgreen4', 'momi_as_nature', 'hyewony88', 'han_gyul.lee', 'bh0503', 'soondi_', 'heumish', 'orol0915', 'carolpsy42', 'l1423202', 'woduddl1', 'hhyerining', 'hyunjin1145', 'calligr04', 'kmd_jeong', 'as.deewhy', 'freehugdj', 'john_n_mary', 'hajaegyu1543', 'abbie_mutd', 'b4sunrise111', 'youone_drq', 'ulsanhani', 'csong1221', 'kmd.ryu', 'cz_0701', 'lansundoctor', 'kim_jungyub', 'gyaaa_aak', 'yuseong1518', 'ytipika', 'springinthegarden', 'peppers_dad_mingu', 'kiacyaksun', 'hjs1023', 'singsong_doc', 'jooheedaaa', 'coruscants', 'o.da_yoon', 'yhkim9898', 'jungtaeleem', 'im_0chory', '0102_1119kd', 'ujin_clinic', 'abyungwoong', 'yonghyun.s', 'jj.seob', '5ung7un', 'parkgyunghun', 'sterilization_', 'mindoong_vindoong', 'iuiu0', 'flydob', 'mousehun', 'hunnn.k', 'kimdaeeok', 'crucian_carp__', 'sejong.sandol.official', 'ggakom', 'lasting_smallscent', 'ejnuyh', 'ajw5251', 'kim_bokk_', 'jhyunyup', 'toktokmedi', 'rayjaang', 'steamfilled_spirit', 'birth_olltwo', 'sang.won.hani', 'bm_k_clinic', 'sunoab', 'crystal_k2357', 'lovlov_ahn', 'refeet_center', 'bjson53', 'the_june___', 'ljhdjhan2529', 'gang__h0', 'kwj_0510', 'eomhyiweon86', 'iyunjung8', 'kim_kidong81', 'jeong.eun_wii', 'jj_heony', 'olzl_e', 'haha.sungwoo', 'mazelinkim', 'vnnihm', 'alswns6387', 'shinheungmedscience', 'kibaek_clinic', 'gdaj_mgbalsan', 'matt12kim', '0jincha', 'jswannn_', 'youl.hyeong', 'hyunho.kim_', '0sta9ramy', 'ss_miiiiniiii', 'integrity_interview', 'fullaccel_chul', 's8muel_', 'no.1deer', 'ohworms', 'youngsam.3', 'l.changseob', 'jaythepark', 'chingood09', 'dolfung_ee', 'gpdnjs1999', 'ysw._._._', 'jiminku', 'stu_kmed22', 'dbsehdrjs_study', 'aipm_tongchi', 'yoxnha', 'ch__yang__', 'onon.93', 'gimjehyeong4683', 'mr_door32', 'gyihjs733', 'brother._.muk', 'kimyoungjun8053', 'sang_hii_', 'kh_limda', 'park_es1', 'cajaseng_', 'songksomd', 'joelhys', 'chkwon816', 'drxxhan', 'monshellton', 'jaewon_august_choi', 'kimyeonjeong0712', 'c_aela', 'loner_0401', 'nanadoc7', 'meletio_jay', 'sangkiyun', 'xemio228', 'miscrophone', 'heej__xx', 'key.michael', 'shy.ped', 'junhohyun0609', 'jkkkch', 'rhonrhon639', 'hi_raniiiii_', 'dr_jayh', 'heedo22', 'ahn.sanghyun.75', 'sangtaee', 'sso_monmon', 'duddnrlg', 'port_able2', 'jung_annie', 'stevek12018', 'namsh27', 'sinyunha695839', 'ingdi_ausflug', 'veil_pale', 'jiyeoninie', 'egskin', 'psdoctorjki', 'yumin2146', 'demichism', 'dermahurray', 'jdvetter25', 'viva_la_chacha', 'simbassickssick', 'zomkki', 'jannyyi', 'jl_2jh_ps', 'dr.yeumhong', 'jnheo', 'mingoon__', 'mrpiglefit', 'chom.h.h', 'h_bummi', 'gijun3374', 'rogue0025.vsf', 'east_jiin', '100percent_jinuuuu', 'medi._.chin', '1dorodong1', 'l.jiyoung', '__songvely___', 'yonseibom_ent', 'h_psy', 'subin_970717', 'ellyhsmoon', 'cha.serin', 'dr.fendi_chen', 'gun__hyung', 'junghwan328', 'sony_the_u_ho', 'jungstagram_1990', '___dr.iven', 'jude_innerdemons', 'jeongmin_oh__', 'encore0311', 'songsy84', 'drjihee', 'k_e0811', 'park_yoja', '23vitruvian', 'ksnm.or.kr', 'sehonna__96', 'mean_gee1201', 'rkdso1123', 'wxx_zynn_01', 'young_joo_kwon', '0.joon_0326', 'nak0602', 'kyungah.seo', 'woodada_julie', 'qj_song', 'choi_.wy', '_imnk', 'an_nyan_hi', 'kimay1298', 'jh_6595', 'happy_greeeen', 'john_kr90', 'kimsehyun0805', 'cutiscura', 'bbaenggis', 'marco.s_18', 'cho2584', 'miniminimi_daily', 'cjads81', 'md_choisungyeol', 'doridungjul', 'saehee__jung', 'jeongwoo1294', 'kimjh21cen', 'nyerinx', 'jw_jake_jung', 'seoah_seoyeon', 'chris1002chh', 'ihnnamkoong', 'gomsalman', 'frumentius7', 'md.the_real', 'study_doctor_dabin', 'medst__', 'youfirstd', 'ddae_ddae_bal', 'minbyungeda', 'mo_bum_u', 'kica370', 'chic._.yeonjae', 'yslee876', 'tedjgnam', 'minjeong03077', 'parkjune84', 'hae5ning', 'diaphony_knu', 'dr._mj_happiness', 'daejungkim69', 'jejangnim', 'ramichoi92', 'rhytksa', 'reason_b1n', 'hoon_i_e', 'ryhryh1231', 'ganheez', 'ducky1117', 'zaizenkim', '_xrayoh_', 'yongjae___k', 'gnu.c', 'shgregchoi', 'violetnpurple', 'hsh6016', 'seunghyeon6301', 'dreamy.jing', 'drchin777', 'zhiruyi16', 'samo_samoy', 'godzerooo', 'letsgaza', 'sunghwan.yoo', 'hyorim_jo', 'seuuung._.y', 'luca_lee_127', 'korean_medical_association', 'hjjnkim', 'erin_cym', 'seungkangyoo', 'hannahsh87', 'ohhyunsss', 'sksxk6', 'lacoonsam', 'syounglee00', 'gjkim_0429', 'litalco_inc', 'lilyrla_0408', 'rogun_0._0_', 'martian248', 'anarkh7_7', 'jwjwjwjjwjjwjjw', 'what_the_ko', 'np.jun', 'huhming_9', 'steven_hyeseungjeong', 'earthsun720', 'from_jinxin', 'kyusikahn', 'scdol8275', 'achilleus_jeong', 'chungblee', 'buffyslaw', 'dr.kim_evidence', 'mh_espi', 'viviansquee', 's_yechxn', 'limjjoo_', 'dudccodii', 'nabiiii', 'djch06', 'sjy.md', 'jjoong007', 'sky511', '_jisuj', 'daeuny_daeun', 'nfcra', 'yeah_e__', 'harrison_korea', 'medicalbamboo', 'nice_dr_parmani', 'febrerosu', 'kuyesl', 'floranunc_', 'kyul_1501', 'hyojeong_1112', '92jinu', 'hamita87', 'jaehyun_hada', 'smin_dani', 'roy_the_sang', 'yellowclinic_hwang_in_hye', 'pseud_o19', 'yohan.kim.73113', 'dr_shim_neuro_pain', 'gunnigunny', 'phgentleman', 'larctv', 'my__nation', 'forestella_0509', 'hannalina_', 'yeoingyeo', '96.jaykim', 'jamsiltiger', 'kyunxcene_', 'yyoonsang', 'dooyoun.hwang', 'imjunhyeog714', 'lavie_jh', 'kkkkim___hyennn', 'junni_jun_', 'medihs2020', 'runningbeauty', 'dkswjddn86', 'embargo.cheongdam', 'pz_sunghoon', 'jaehyeonjeong', '_jooowon_', 'yerlan_kz_doctor', 'seunghwan_moon', 'dr.zarephath', 'byfgo', 'ps_dr.gustermonte', 'kimminhyoida', 'taekyun_up', 'bmwgdoc', 'leflaive_han', 'dr.altairys', 'drshawn', 'k.mini_jh', 'heejini_jang', '1ly_grace', '_js__choi', 'chusg91', 'howard_starkiv', '_d.o.c.kang_', 'y__j______', 'j_w_min', 'alfn104', 'lodestar.kr', 'psdr__park', 'drmikechin', 'yein_annechoi', 'seokhee_hwang', 'ps_dr_odm', 'minseob_95', 'medical_mavericks_', 'chaeng_o1', 'upimhzfyjomltohjy', 'goalstudio_korea', 'min.doc', 'yellow_nebula', 'avec_le_temps', 'psdr.hyemi', 'medijob_official', 'always_yeoni', 'bradbanghyun', 'bab_3mm', 'nahyun_zzugul', 'soom_nii_ii', 'doctor_k_1571', 'drkdd9', 'wbchangmd', 'sewon_worldbest', 'issue_blue', 'yveschoi', 'md_central', 'newmedia_missionary', 'national_medical_center', 'osj870114', 'gimweonbin750', 'o_dj.ent', 'megrezz_', 'hebronderm', 'jinmi0422', 'mat_zart_', 'zhl_olneee', 'gash_dev', 'yeonnnniiiii', 'dongjae559', 'david.jw.kim', 'dbs7628903', 'c_mooky', 'ogana_', 'haew0nii', 'superkjw', '1023__jy', 'jiwonastrid', 'emily_jujube', 'didung64', 'mon_etoile_sean', 'mctwist720', 'tae_hyeong___', 'gomin_jimin', 'dr_bbbig', 'bigmacset', 'jsamsungent', 'stamp4118', 'cool_daddy_kt', 'jinwon0629', 'dnewdnew', 'talkingdocs', 'leejunehyuk_00', 's.heun_s2', '__drfit', 'jannne_9', 'itaewon_skin', 'k.han_kyu', 'yangtae__', 'h_plastic_surgery', 'hyungjun5929', 'dr_deepflow', 'y_utrue', 'nk_derma', 'scholes_always', 'mooook__e', 'changhyo.bae', 'yusungy', 'dr.jeon_', '_____y95yr', 'hero9022', 'jiheaaaa', 'gihoonnnn', 'bhumble54', 'ssun0618', 'mahalo2023', 'bykimmby', 'woncheol.l', 'yujjjin____', 'apricot_jam__', 'dodohongdodo', 'empirics', 'eunah.han.1', 'ro_giiiiiiii', 'bella_jsun2', '2decho_tte', 'joon462', 'gy___p', 'ysjoo811', 'oooh209', 'dr.kimjiyoung', 'andrea_bskim', 'gm_8.21', 'amc_seoul', 'lovejjun__', 'woogi__e', 'osdoc_h', 'm1n_joonee', 'timetowhistle', 'forme_ps_clinic_dr', 'binge_wook', '5jin_hyukk', 'oeipish327', 'kordunam', 'yimdonchoi', 'zihyun.song', 'tommykim95', 'jolin1019_', 'bright_and_true', 'sunji_no_study', 'kim.youngin', 'hyeonji_hyeonji', 'that_glorious_forehead', 'kyunhoshin', 'sinjunyeong8', 'ym.co.kr', 'avantas88', 'kimchangjune01', 'irene.now_kwon', 'ttonttanttun', 'choco_pigg', 'junbaik_', 'foodtherapy_by_kiho', 'gh_sy_love', 'jhlee316', 'kumran_pp', 'seum7667', 'bulgogi233', 'jclawmall', 'thora__thora', 'cupcup21__72', 'nurifineman', 's.eun411', 'mindong.s', 'jiyeon_dbd', 'yongseoki_', 'cosmosrbloomin', 'genie__gyunny', 'neuropeptide_yy', 'astramir90', 'time8707', 'jooonp', 'good_doctor_networks', 'oreoooreoo', 'key_mon__', 'realllllxmaetamong', 'bomi471', 'chu_hongmin', 'hwistein', 'advilyy', 'rose_378219', 'yeon__uk', 'sangsoo6177', 'yangdagweon', 'dr_ohdoojong', 'jinyblaer', 'seunghan514', 'jkm_nara', 'dolce_gunbana', 'go_jaesung', 'medical_hsh', 'a943', 'huuuyytt_see', 'fi__ni', 'poetic_siliconvalley', 'leejun19999', 'shyuni_story', 'mo.6___iron', 'dotorida34', 'duvespe', 'kimnamwoo_1021', 'mikasus777', 'wjh9088', 'cb_iiina', 'aleslyfelde89', 'heyxxrosy', 'hamamook', 'dohui031104', 'just.ordinary.picture', 'j__00__00__j', 'manstoneurology', 'j.gyeongcun', 'coffee_white3', 'ssophiaim', 'minkyeongc', 'doctorquokka', 'drcarecompany_ceo', 'chang_hwan', 'honey._.hunter', 'djaska25423', 'wangjjangik', 'jae0_b', 'green_eryy', 'jungmin.lee.1840', 'garden_you', 'eunyoungjen', 'imeunhwa7821', 'david870815', 'lucy_amaraa', 'gimgyuho249', 'bull_moth', 'dabangchoco', 'in_joyourlife', 'dewae75', 'dayeong642', 'yell0w_mete0r', 'goodday2iu', 'j_ook_kkk', 'jin.s303', 'luvloblov.e', 'albert_jylee', 'hawking_kim', 'itssyonineko', 'pure20836', 'instaanham_', 'saetgang_', 'a__watni', '__my__ocean', 'rbjtnfdnadv', 'judijjang1010', 'aisha.jie', 'june_121802', 'sa3080', 'jykim0122', 'mkhw_301', 'scented.h', 'junghyun.cho.777', 'ej_hong_', 'stuhrrgeeeon', 'jeje821618', 'h.___.kyo', 'choijanjin', 'dhtnghd', 'together_road', 'reinalorina', 'soonoo.k', 'guang3680603', 'rune_moren', 'seogwangseok1101', 'lmnsdy', 'a_prayer_of_victory', 'vndn000', 'u_inus', 'barley_1104', 'choks7267', 'bawuny', 'chae_han_', 'w_jooon', 'oooooop78', 'hoomi_c', 'katekate1130', 'field_sophip', 'lnddavincii', 'gimseona549_merryflower', 'eunsung1121', 'john.hy.lee', 'soobin0905', 'junginhwan1224', 'k_jonguk92', 'pelllllllong', 'myunghoon3167', 'qqpp010131', 'alladdiinbb', 'peter_sukbum_kim', '199x2229', 'myosu_official', 'bkluvvv74', 'vista_eye_clinic', 'nursing_zoi', 'tngus201', '1_n_oonly', 'chaekyubok', 'hy_kim00', 'teacher_ki', 'dana_jeong', 'btongee', 'hkp810', 'ssokssoki', 'dr.smileyface_catherine', 'jinu.gwak1030', 'he.rani10', 'hwang_changhyeok', 'hdasg560', '_sigmamu', 'hj.joseph.kim.md', 'rainbow.wwwww', 'myeongji6945', 'cheolhany', 'kho_supermoon', 'medinterio', 'tr.kang_', 'kkang_yj_91', 'pass3ng3r13', 'kim_unknown98', 'cocorubycocoruby', 'premed.o2', '35598f_', 'ym.sc', 'hyeaku_lee', 'vinterkd', 'ncxjsdnjdsn', 'jjklark80', 'kkjjklk', 'aesukki9', 'madalyn_travel', 'bbboo6767', 'meta_journey_kor', 'sjdfhguwi3', 'euni7290', 'im_nan._.y', '2_so_heun', 'doc.cw.sg', 'yunji.book.48586385', 'mojosa25', 'a.song.of.purple.summer_', 'siennadelos', 'cn_smartdoctor', 'dkdld012', 's.y_2013', 'qtqtwgxuw', 'smithhh.__.7', 'j___ys715', 'gyupyl', 'baeseongjin4035', 'sindonghun893', 'dae_soung', 'bts_1700', 'dongdonghrr', 'medical__student_2023', 'raon.medical_official', 'adhd_med_student', 'dyt.salihgurel', 'skysoul486', '0410kh', 'hkinsu433', 'butchery_midam', 'dorrammong_98', 'shinsegae_welding', '333ryeong', 'hyunjin060409', 'cerchio___', 'kim.w.h.99', 'roselim16', 'seungwook_more', 'leadersnurse.official', 'cheree3653', 'jxnwxxng', 'baeg_jongbeom', 'imthewilll', 'ttukkung85', 'b.bong_2', 'self_n_consulting', 'yuna._.0727', 'oilstraight_xx', 'khkimmmm', 'parkj2h0', 'zellyhyhy', '_funocuenta909_', 'jjisan_jang', 'zero_k_14', 'bluebluebluuee', 'lifeis_bc', 'cafeboy20', 'alsrb789789', '_minjeeeeeeee', 'djawl00', 'yellow_meteor', 'c.haeppy', 'grandbseye_', 'everymomentwith', 'park_lou', 'wys_filnst', 'tttnatna', 'awesome_lazy_penguin', 'spongrrr', 'hyesuu26', '__oddl_', 'boyeon155', 'choi_fibre', 'chanwoong_jang', 'jiung_jay', 'hevarner', 'not_easy_but_not_impossible', '1kang_team', 'dormickvemr', '1d_woong', 'imiseon97', 'jingyu.lee_', 'oh__yj20', 'dikego.0', 'jjin_m_23', 'usus_oop39', 'autumns_weder', 'mj_syper', 'medickim', 'shamekaranger', 'kida_dental_association', 'lexington9191', 'hclass_sua', 'vvv_bks', 'glorycho2020', 'day_vy_day', 'seongwonjae', 'jessie_thestar', 'ibox365', 'crystal_root_', 'cherish_yoo21', 'jihwan_k0314', 'cidowpvkw', 'maxsein37', 'boyoung462', 'eokman810131', 'hanjeajae', 'kd_koh', 'broccoli0723', 'yeoulnaru2021', 'teamk_ceo_lui', 'brothersuv', 'kyuri_dla', 'jhrim2022', 'mi_mi_seong', 'toyou2002t', 'seosyeun24', 'speaklovesoftly', 'navlong_save', 'mouda_platform', 'happyvillagers', 'shkim7743', 'neo1714', 'ish_cku', 'hdkim6173', 'qwe.rt010101', 'koonja_publishers', 'prime33_hong', 'maedduk2', 'hs891026']

    ##2. 유저 분할
    total_user_infos_group = divide_user_infos_list(user_infos_list, group_size=1)

    ##3. db 발송
    send_total_message(total_user_infos_group, text, project_name=project)
