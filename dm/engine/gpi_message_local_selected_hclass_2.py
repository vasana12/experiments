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
    account_setting_info = INSTA_ACCOUNT_OBJ.select_and_update_user(username="mawilson7763", client_name=None)
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
    user_infos_list = ['amc_seoul', 'lovejjun__', 'woogi__e', 'osdoc_h', 'm1n_joonee', 'timetowhistle', 'forme_ps_clinic_dr', 'binge_wook', '5jin_hyukk', 'oeipish327', 'kordunam', 'yimdonchoi', 'zihyun.song', 'tommykim95', 'jolin1019_', 'bright_and_true', 'sunji_no_study', 'kim.youngin', 'hyeonji_hyeonji', 'that_glorious_forehead', 'kyunhoshin', 'sinjunyeong8', 'ym.co.kr', 'avantas88', 'kimchangjune01', 'irene.now_kwon', 'ttonttanttun', 'choco_pigg', 'junbaik_', 'foodtherapy_by_kiho', 'gh_sy_love', 'jhlee316', 'kumran_pp', 'seum7667', 'bulgogi233', 'jclawmall', 'thora__thora', 'cupcup21__72', 'nurifineman', 's.eun411', 'mindong.s', 'jiyeon_dbd', 'yongseoki_', 'cosmosrbloomin', 'genie__gyunny', 'neuropeptide_yy', 'astramir90', 'time8707', 'jooonp', 'good_doctor_networks', 'oreoooreoo', 'key_mon__', 'realllllxmaetamong', 'bomi471', 'chu_hongmin', 'hwistein', 'advilyy', 'rose_378219', 'yeon__uk', 'sangsoo6177', 'yangdagweon', 'dr_ohdoojong', 'jinyblaer', 'seunghan514', 'jkm_nara', 'dolce_gunbana', 'go_jaesung', 'medical_hsh', 'a943', 'huuuyytt_see', 'fi__ni', 'poetic_siliconvalley', 'leejun19999', 'shyuni_story', 'mo.6___iron', 'dotorida34', 'duvespe', 'kimnamwoo_1021', 'mikasus777', 'wjh9088', 'cb_iiina', 'aleslyfelde89', 'heyxxrosy', 'hamamook', 'dohui031104', 'just.ordinary.picture', 'j__00__00__j', 'manstoneurology', 'j.gyeongcun', 'coffee_white3', 'ssophiaim', 'minkyeongc', 'doctorquokka', 'drcarecompany_ceo', 'chang_hwan', 'honey._.hunter', 'djaska25423', 'wangjjangik', 'jae0_b', 'green_eryy', 'jungmin.lee.1840', 'garden_you', 'eunyoungjen', 'imeunhwa7821', 'david870815', 'lucy_amaraa', 'gimgyuho249', 'bull_moth', 'dabangchoco', 'in_joyourlife', 'dewae75', 'dayeong642', 'yell0w_mete0r', 'goodday2iu', 'j_ook_kkk', 'jin.s303', 'luvloblov.e', 'albert_jylee', 'hawking_kim', 'itssyonineko', 'pure20836', 'instaanham_', 'saetgang_', 'a__watni', '__my__ocean', 'rbjtnfdnadv', 'judijjang1010', 'aisha.jie', 'june_121802', 'sa3080', 'jykim0122', 'mkhw_301', 'scented.h', 'junghyun.cho.777', 'ej_hong_', 'stuhrrgeeeon', 'jeje821618', 'h.___.kyo', 'choijanjin', 'dhtnghd', 'together_road', 'reinalorina', 'soonoo.k', 'guang3680603', 'rune_moren', 'seogwangseok1101', 'lmnsdy', 'a_prayer_of_victory', 'vndn000', 'u_inus', 'barley_1104', 'choks7267', 'bawuny', 'chae_han_', 'w_jooon', 'oooooop78', 'hoomi_c', 'katekate1130', 'field_sophip', 'lnddavincii', 'gimseona549_merryflower', 'eunsung1121', 'john.hy.lee', 'soobin0905', 'junginhwan1224', 'k_jonguk92', 'pelllllllong', 'myunghoon3167', 'qqpp010131', 'alladdiinbb', 'peter_sukbum_kim', '199x2229', 'myosu_official', 'bkluvvv74', 'vista_eye_clinic', 'nursing_zoi', 'tngus201', '1_n_oonly', 'chaekyubok', 'hy_kim00', 'teacher_ki', 'dana_jeong', 'btongee', 'hkp810', 'ssokssoki', 'dr.smileyface_catherine', 'jinu.gwak1030', 'he.rani10', 'hwang_changhyeok', 'hdasg560', '_sigmamu', 'hj.joseph.kim.md', 'rainbow.wwwww', 'myeongji6945', 'cheolhany', 'kho_supermoon', 'medinterio', 'tr.kang_', 'kkang_yj_91', 'pass3ng3r13', 'kim_unknown98', 'cocorubycocoruby', 'premed.o2', '35598f_', 'ym.sc', 'hyeaku_lee', 'vinterkd', 'ncxjsdnjdsn', 'jjklark80', 'kkjjklk', 'aesukki9', 'madalyn_travel', 'bbboo6767', 'meta_journey_kor', 'sjdfhguwi3', 'euni7290', 'im_nan._.y', '2_so_heun', 'doc.cw.sg', 'yunji.book.48586385', 'mojosa25', 'a.song.of.purple.summer_', 'siennadelos', 'cn_smartdoctor', 'dkdld012', 's.y_2013', 'qtqtwgxuw', 'smithhh.__.7', 'j___ys715', 'gyupyl', 'baeseongjin4035', 'sindonghun893', 'dae_soung', 'bts_1700', 'dongdonghrr', 'medical__student_2023', 'raon.medical_official', 'adhd_med_student', 'dyt.salihgurel', 'skysoul486', '0410kh', 'hkinsu433', 'butchery_midam', 'dorrammong_98', 'shinsegae_welding', '333ryeong', 'hyunjin060409', 'cerchio___', 'kim.w.h.99', 'roselim16', 'seungwook_more', 'leadersnurse.official', 'cheree3653', 'jxnwxxng', 'baeg_jongbeom', 'imthewilll', 'ttukkung85', 'b.bong_2', 'self_n_consulting', 'yuna._.0727', 'oilstraight_xx', 'khkimmmm', 'parkj2h0', 'zellyhyhy', '_funocuenta909_', 'jjisan_jang', 'zero_k_14', 'bluebluebluuee', 'lifeis_bc', 'cafeboy20', 'alsrb789789', '_minjeeeeeeee', 'djawl00', 'yellow_meteor', 'c.haeppy', 'grandbseye_', 'everymomentwith', 'park_lou', 'wys_filnst', 'tttnatna', 'awesome_lazy_penguin', 'spongrrr', 'hyesuu26', '__oddl_', 'boyeon155', 'choi_fibre', 'chanwoong_jang', 'jiung_jay', 'hevarner', 'not_easy_but_not_impossible', '1kang_team', 'dormickvemr', '1d_woong', 'imiseon97', 'jingyu.lee_', 'oh__yj20', 'dikego.0', 'jjin_m_23', 'usus_oop39', 'autumns_weder', 'mj_syper', 'medickim', 'shamekaranger', 'kida_dental_association', 'lexington9191', 'hclass_sua', 'vvv_bks', 'glorycho2020', 'day_vy_day', 'seongwonjae', 'jessie_thestar', 'ibox365', 'crystal_root_', 'cherish_yoo21', 'jihwan_k0314', 'cidowpvkw', 'maxsein37', 'boyoung462', 'eokman810131', 'hanjeajae', 'kd_koh', 'broccoli0723', 'yeoulnaru2021', 'teamk_ceo_lui', 'brothersuv', 'kyuri_dla', 'jhrim2022', 'mi_mi_seong', 'toyou2002t', 'seosyeun24', 'speaklovesoftly', 'navlong_save', 'mouda_platform', 'happyvillagers', 'shkim7743', 'neo1714', 'ish_cku', 'hdkim6173', 'qwe.rt010101', 'koonja_publishers', 'prime33_hong', 'maedduk2', 'hs891026']
    print(len(user_infos_list))
    ##2. 유저 분할
    total_user_infos_group = divide_user_infos_list(user_infos_list, group_size=1)

    ##3. db 발송
    send_total_message(total_user_infos_group, text, project_name=project)
