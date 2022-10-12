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

host, port, proxy_username, proxy_password = "mobile.ipb.cloud", "7777", "customer-fydh21628401-asn-20057-sessid-RcPU-sesstime-1", "awR4Sad2t"
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
            user_id = get_user_id_by_db(username)
            valid_user_id = get_user_by_id_gpi(user_id)
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
    project = "hclass_10_11_filter_1"

    ##파일이름
    filename = "hclass_10_11_filter_1"
    project_start_date = "2022-10-07"

    text = get_dm_source.get_source_message(f"{project}.txt")
    # user_infos_list = user_split("""['_xxngxxn', 'im_jiw', 'c_h_21_2', 'funsurf_yangyang', 'huit_kr', 'stella_yuju', 'yoga_hana.k', 'jinny.suh.00', 'yogini_who_loves_golf', 'chunsia', 'royallife.kim', 'ena_luv_j', 'hennie_al', 'dr.body.official', 'sports_bong', 'yoon_pila', 'yoga_hyuna', 'siwa_yoon', 'sangvely_luv', 'darliyoga_', 'lizzy.doit', 'hyep__.__', 'vidya__yoga', 'solyyyy_', 's__ung.e', 'haho_haaahooo_o', 'jisu_like', 'eu____b', 'seon_eunsisters_mom', 'euun_jinn', 'diet_hye65', 'kangbodeok_daom', 'nuskin_bigstory', 'bodyfit_yul', 'yang_songhee_', 'iam_sia_', 'kang_16.04.12', 'jami.zip', 'sunny_choi_0930', '810521sun', 'ppark_cc_', 'oneuldo_yoga_pilates', 'marinesnow1212', 'bonbonbubble_', 'nana_readerrun', 'ryeoeun.kwon', 'youyon___', 'yn_s_1230', 'kangsuk09', '__domdomi', 's0yun', 'lim_onion', 'pila.jian', 'so._.0__0', 'soy_onadiet', '2tok_tok2', 'bini__potato_mom', 'haru35698', '0_0_riii', 'a.t.sr', 'park_sang_jeong', 'oh_a.sis', 'hyelin_yoga', 'reflying_hr', 'aitchxh', 'ssingbori_seohyun', 'rom__romrom', 'varunayoga1004', 'kkkcare', 'parsley_reviews', 'inner_jenny', 'chaem.co.kr', 'lolhana1231', 'yooooooooom_', 'bbn2nee', 'move_ms222', 'n.aelii', 'saena_163', 'jiah_0527', 'alphapurple', 'heeyoonyoga', 'u_uri__', 'piline_hy', 'mmichelin_diet', 'yeseul_workout', 'studio_masil_bp', 'haanvit', '2ogram', '__a_yeon', 'so___ri_', 'steady_hun_', 'daypilates_', 'basic_pt_studi0', 'seong2un', 'celeblab_official', 'haranxs', 'pilates0_j', 'k_yeonju_', 'artistmimicha', 'groov.jeju', 'store64602019', 'jin_jooooo_', 'hyejung_happy', 'gomunju', '29flower30', 'k_kratte', 'playbenjamas', '1.5iterations', 'yogavna_vayu', 'beomq_building', 'ageture0607', 'yoganamu_momo', 'ra_ni_star', 'kwonmina_pilates', 'yoga_jolly', 'harvesturbo', 'b1ozrx8emdu6', 'namaskar_restaurant', '1limjungsun', 'ayurgong', 'jisun.ardor', 'nabi_yoga_the_om', 'tina__yogini', 'heeaee__s2', 'dieter.dh', 'kim.pearl._.a', 'yoga_appletree', '_whereorwhen', 'han_yujin88', 'artlovervanrijn', 'yoga.love.yoo', 'mi_ri_jjang_', 'yujuuuuun', 'yoga_momam', 'jjino_pp', 'taeriblossom', '__yh424', 'pinnnymph', '_sujinning', 'tsparkts', '9se._.bin9', 'simsungeun2727', 'yuhyel_', 'angelayoga_yui', 'vip_ssonim', 'dolmal_creator', 'atti____j', 'ha_eun_seol', 'dailydose_gwen', '55555j_', 'eunrabbit0_0', 'seyeon6711', 'kkommizi', 'hyen___k_', 'jhwan.e_', 'nanna0333', 'from_lumi', 'hong.ssseung', 'birdieliau', 'yoonlypilates', 'yoo_jin_love', 'yogi_hyonii', 'yohan6501', 'yi_seul92', 'yoginihi_', 'yogaon_zen', 'yogafit_flywithyou', 'yeon2vely', 'yennkai_', 'y.b_jjung', 'xixixixiri', 'west_delay', 'valvue.22', 'u_ming.z_2nd', 'selena_kang_', 'rvd_fit', 'rumy5876', 'rumiearth', 'rlo_or_jo', 'rangedaykorea_hg', 'r_h2sse0', 'qo_op____', 'pjungwon0224', 'pd__pi', 'okaeri2525fitness', 'mr_yyanggeng', 'minampocha', 'me_florette', 'maryss_93_', 'lv.1112', 'lukenbyjay', 'lucky_haejin', 'lcb_n', 'kkim__0', 'josu_hyeoun', 'jiheeing_', 'i.seungah.you', 'hwangseoyeong826', 'hoonyhooni2', 'holcombsxr.lelia', 'happynew100days', 'han_ju_a', 'gy_1201_', 'from_nine_', 'edgar.de.gas', 'e.yunna', 'demi.in.sydney', 'dear.comma_', 'chriisdacanha', 'choe_hui_yeong', 'changkzs.wanda', 'brandnew1004my', 'bodyupmk', 'berryfsa.juliette', 'became.a.yogi', 'b1.__.ju', 'apple.bottle', 'aop_hsj', 'aa.___.ra', '_m_____ay_', '_hhhjin', '_ha___0', '_chaechae_ringg0_', '_bonnybunny', '______11023', '_._.oo_o', '5150hero2', '236789.5', '28balance.workout', 'yojine.o_c', 'yogihihi_', 'soraafit', 'rainbow.lts', 'junghayoon_', 'jieun.yogalife', 'workout_jigwan', 'studio_kula', 'sivanandayoga_hannam', 'sara.flower.yoga', 'monii.morning', 'mans_fits', 'kimssun01', 'johnny_handstanding', 'im_jennyyoga', 'haruyoga_', 'g2g_dyb', 'commonstudio_kr', '__27th_may', 'jejuspinning', 'yogini_moaa', 'suhyeon.love', 'shinse_yoga', 'rajahata486', 'lunafitory', 'healthy.yoginimom', '_yijm_yoga', '3.26_hg', 'tomato0417_j', 'eunheehur', 'choichamp.numik', 'chitta_aria', 'yoga__yeon', 'sodamyoga_online', 'jh_armbalance', 'in02_pole', 'z_bly_o', 'sim.kong_log', '_lifeisyoga', 'shriveda_ayurveda_', 'gangnam_nadiayoga', 'bonarich212', 'hearty.lifestyle', 'sinae.jung.7', 'sojung_kim_', 'wildergmq.angela', 'oceanpacific_official', 'mirisu_', 'letape.korea', 'juarezlhi.darla', 'jihee____', 'han_ungi', 'vvljn____', 'rxorn3x', 'oo2.12oo', 'jo_yoonseo_', 'xuxunx', 'seo_young_h', 'rainmaker_0622', 'hee_hee_chu', 'choijk2690', '911111hana', '2._j0', 'jywsj', 'ax._.milk', 'leexeoin', 'jxxyul', 'ennn__00', 'berry_vely_s2', '_96.s2', 'googlewigglegoggle', 'boy2on', 'yoga.one88', 'shineglam_of', 'january_cui', 'appointment_studio', '_belle_j', 'yogiyogibo', 'sooooolbit', 'potaro_hibinokiroku', 'pado_so_ri', 'move.kdh', 'ji_minns_', 'h_jung2_4', 'b2.my___yezy', '_n.rae', '_gelucke8om_', 'yogaseom', 'vitaminamina.gram', 'theintrovertsyoga', 'theclassicpilates', 'tan__zzang', 'susanhchong', 's2soy_', 'numinousyoga', 'nametag_design', 'mingzi552', 'kyliekpyoga', 'im_ggum', 'dave_yogastudio', 'bit_na._.j', 'artsyoginista', 'ado_m1n.g', '_e_ghaempanah_', '_daon_yun_', 'yogini_vanessa_', 'l3na.kim', 'healthboygym_sinbu', '100_kg___', 'yoga_chiangmai', 'yomdy_healthy', 'yogi_0416', 'yogasnowboarder', 'yoga_jeong', 'xodoa4931', 'uotds4831', 'uiope3781', 'uiopr4831', 'tps2740', 'toroe3712', 'too_too_lovely', 'the_heart_trainer', 't.black_cat', 'sunshine_hy_', 'sunshinebungee', 'staryoga_jian', 'ssangdo_nam', 'sophie_seoul_yoga', 'soop_foret', 'smtiger_gym_', 'smk_dancewear_kr', 'sjpqezov851887', 'shuuvayu', 'seven.seasworld', 'shareyoga_su', 'sayu_yoga06', 'sansojiwon', 's1o._3', 'resortlab', 'practicingyoga', 'plates._.mk', 'pilaroum', 'piggie_sh', 'only_joaa', 'o2healgarden', 'natsuki_trsw', 'natalya.levenets', 'momoj_dress_shop', 'merci_yoga_', 'mayomooni', 'mcleanfor.gabriela', 'man._.dooo', 'liyong_golf', 'lilyandgiru', 'lini_andyou_3', 'lady_lara_0201', 'kirin.shoes', 'kim_hyeyun2225', 'kangs_note', 'juju__kim', 'journey__2', 'jinyoung_gram_', 'jejuspinning', 'j_mean816', 'j.utopiaa', 'hongseongho493', 'heartfulness_hana', 'healthboygym_sinbu', 'hamtori_13', 'gr2shmd', 'fodos7890', 'flora__bonnie_', 'dosoa3821', 'dayayoga_studio', 'daheechoi_', 'crossfit_dong_dong', 'climbawaykay', 'cind.yoga', 'chs.dht', 'choijeesoo_', 'chjj818', 'chichang43', 'ca_niss', 'body_channel13', 'beyoum_jiminyeo', 'bettervely__', 'beaver_0815', 'bbopole', 'be_um_yoga', 'bb_pilayo', 'bayo_yoga_', 'ashylist_studio', 'anyunheeyoga_pilates', 'aosie3721', '_ya_89', '_love.of.fate', '_f.soeun', '5second_da', '41.0mn', '_suuhyun', 'suziooi', 'princess_ana_liz_official', 'yunseo_studio', 'yong_yong.e', 'yogini__hyuna', 'yoga__yeona', 'yewon___0830', 'yantisong123', 'xa1_health', 'vonamyo', 'viiinnnnnnnn', 'tlguss_02', 'tlight_2g0_', 'taoyoga_saerom2', 'susuyoga_', 'suziooi', 'suhakuyoga', 'studio__cuba', 'soru_____', 'shauntareny', 'see_hyoung', 'saya_yoga.222', 'sang__illll', 'samboogi', 'r1m.o1', 'pila_yogini', 'parkyonghyun77', 'p_draw___', 'p_y_society_cheomdan', 'p_log100', 'on_yogastudio', 'min.gyu7938', 'mi_yoga00', 'mi_so.song', 'lo_reve_design', 'lixm_fit', 'kbom__2.2', 'jungminby', 'jstar.fitness', 'jonggak_ypilatesnyoga', 'jjjjaaaaeeeee', 'jinhaepilates', 'jihye_19_5', 'jee_925', 'jae.yoga.pilates', 'iooi__j', 'imayogihk', 'hoho.plus', 'hj__young', 'hanayxj', 'hamg_project', 'h0lizy', 'gamja__c', 'gabayoga_kr', 'foundy.me', 'flyingyogigi', 'develop_rianhj', 'ddouble116', 'dagym_yoo', 'cracker_______', 'cho_sung_ju', 'casam010', 'byul_.dove', 'bong9_j', 'bodycontrol_training', 'bingsoobin9_', 'aude_yoga', 'a_minacle', '2_0518', 'basic_lesson', 'zingong_yong', 'zelda_park', 'you_zin', 'yogadana_fit', 'yogi_seoul', 'yoga_jessica_', 'ye._.won._.s', 'y.u.u.j', 'wayto.om', 'vividahro', 'twin.su', 'suzyinyoga', 'sunsetszin', 'sujannee', 'stella.hanbuyl', 'ssonghhaa', 'showfit_photography', 'seul.___.gi_', 'serene_serenity', 'ruciel_mall_5570', 'ram___zzi', 'raan_yoga_pilates0410', 'quickreview7', 'pole_jiya', 'pilatesh_jenny', 'pinkhara9', 'pearyyoga', 'onsaelove', 'nunnunannaa', 'nooo_dumbbell', 'nextfitness_seok', 'merry_yoga_', 'mandoo._.river', 'labeaute_mor', 'l_ch77', 'kongeungkyung', 'ko_ko_workout', 'khulan__________', 'k.kyu_0715', 'jung_.potato', 'joo___h94', 'ji_n_n0', 'j.jyr__', 'i_park.commu', 'herejisoois', 'hee_s_new_s', 'haejin__', 'gyeol.draweat', 'gpdnjs_91', 'freediver_bbotamin', 'fit.adrop', 'esperlmall2', 'diptir_yoga', 'danbusa_sava', 'coach.mino', 'cldud1234', 'choichanheekr', 'choichanhee.kr', 'bodynsol_sd', 'bo_k._.y', 'beaumondepepe', 'barasona_coffee_bakery_yoga', 'backpack_of_artist', 'ajna_inyoung', '__the.reve', '7_9_63__', 'uki12318', 'zkzkzlzlzizi', 'zieunyoga', 'yujin.pilates', 'yoga_lyn_', 'yogajini_draw', 'yoga_yeonju', 'yeonjung1575', 'yejimon.0_0.s', 'w0_n__', 'today.tomorrow.for.us', 'sun_vely29', 'shine_ayurveda', 's__keun_', 's2.y__6', 'ruhen_yoga.pilates', 'roum_yogapilates5', 'rewater4me', 'reboooting_homt', 'pye__yep', 'plus_7200', 'pilatesori_', 'paty0418', 'p.p.e.m', 'ol__may', 'nini__s2_', 'nataraja_ek', 'nalyo_bonnyfit_ss', 'min_mma02', 'min.d_yoga', 'luv__cream', 'luv.my_body', 'lsuhahl', 'loel.u', 'llla_goodmorning', 'kori_liuwa', 'kikikisuinisuic', 'khj_153', 'k._.nnani', 'jw0ne1004', 'judocrossfit', 'jodeodeok', 'jjeong2__', 'jjcol_d', 'jj_ell_y', 'jayge.bro_offcial', 'irai_yoga', 'i__end.wl_', 'i.mdust', 'hyunju_95', 'hyeonii_s', 'honja_homt', 'hodie_kr', 'hihula275', 'ganji_diet', 'g0220_g', 'flowermin_01', 'filmvictor', 'fashion_198204', 'diego_wave_yogi', 'ddu___bi', 'ddong_ggo_mong', 'daom_changwon', 'danahotyoga_816', 'd.hye0', 'd.__.hxxn', 'cuiryeong', 'choij.ye', 'chang._.55s', 'ch_xng', 'celine__lim_', 'ch.seol', 'casino_vip_model', 'bondy_yoga_pilates', 'bodychannel.__.ht', 'bigtree_tattoo', 'big_dong_2_', 'b0rm_', 'ayurveda_yoga_kr', 'arnayoga_jh', 'ahepf79', 'agni_yoga_pilates3', 'actingcoach_jung', 'a.yu_xx', '_changjae_', '__fitness_99_spaseoul_eden', '92brianna_cho', '3.l7kg', '2loui_s', 'ye_ri_ming', 'yogabeot__', 'su.jin0223', 'yoon_hyung_jun', 'yln__o', 'yoga_i.ge', 'yogasis_official', 'yogafulnesslife', 'x_xxey_', 'wonyoga.pilates', 'westglass_', 'theshotyoga', 'teong12', 'tattooing_nature', 'sosohan_yoga', 'sooborru.yoga', 'shes_yoga', 'seul_gi0620', 'sbodyfit_yangju', 'sadhguru.hangeul', 'rattan_always', 'raku___uu', 'rabbit_jjhh', 'r_ddung', 'r.kdb.s0', 'planbfitness2', 'pilates.chae', 'pilaby.youngshin', 'owenhab.earnestine']""")
    # print(user_infos_list)
    # input()
    user_infos_list = ['pinnnymph', '_sujinning', 'tsparkts', '9se._.bin9', 'simsungeun2727', 'yuhyel_', 'angelayoga_yui', 'vip_ssonim', 'dolmal_creator', 'atti____j', 'ha_eun_seol', 'dailydose_gwen', '55555j_', 'eunrabbit0_0', 'seyeon6711', 'kkommizi', 'hyen___k_', 'jhwan.e_', 'nanna0333', 'from_lumi', 'hong.ssseung', 'birdieliau', 'yoonlypilates', 'yoo_jin_love', 'yogi_hyonii', 'yohan6501', 'yi_seul92', 'yoginihi_', 'yogaon_zen', 'yogafit_flywithyou', 'yeon2vely', 'yennkai_', 'y.b_jjung', 'xixixixiri', 'west_delay', 'valvue.22', 'u_ming.z_2nd', 'selena_kang_', 'rvd_fit', 'rumy5876', 'rumiearth', 'rlo_or_jo', 'rangedaykorea_hg', 'r_h2sse0', 'qo_op____', 'pjungwon0224', 'pd__pi', 'okaeri2525fitness', 'mr_yyanggeng', 'minampocha', 'me_florette', 'maryss_93_', 'lv.1112', 'lukenbyjay', 'lucky_haejin', 'lcb_n', 'kkim__0', 'josu_hyeoun', 'jiheeing_', 'i.seungah.you', 'hwangseoyeong826', 'hoonyhooni2', 'holcombsxr.lelia', 'happynew100days', 'han_ju_a', 'gy_1201_', 'from_nine_', 'edgar.de.gas', 'e.yunna', 'demi.in.sydney', 'dear.comma_', 'chriisdacanha', 'choe_hui_yeong', 'changkzs.wanda', 'brandnew1004my', 'bodyupmk', 'berryfsa.juliette', 'became.a.yogi', 'b1.__.ju', 'apple.bottle', 'aop_hsj', 'aa.___.ra', '_m_____ay_', '_hhhjin', '_ha___0', '_chaechae_ringg0_', '_bonnybunny', '______11023', '_._.oo_o', '5150hero2', '236789.5', '28balance.workout', 'yojine.o_c', 'yogihihi_', 'soraafit', 'rainbow.lts', 'junghayoon_', 'jieun.yogalife', 'workout_jigwan', 'studio_kula', 'sivanandayoga_hannam', 'sara.flower.yoga', 'monii.morning', 'mans_fits', 'kimssun01', 'johnny_handstanding', 'im_jennyyoga', 'haruyoga_', 'g2g_dyb', 'commonstudio_kr', '__27th_may', 'jejuspinning', 'yogini_moaa', 'suhyeon.love', 'shinse_yoga', 'rajahata486', 'lunafitory', 'healthy.yoginimom', '_yijm_yoga', '3.26_hg', 'tomato0417_j', 'eunheehur', 'choichamp.numik', 'chitta_aria', 'yoga__yeon', 'sodamyoga_online', 'jh_armbalance', 'in02_pole', 'z_bly_o', 'sim.kong_log', '_lifeisyoga', 'shriveda_ayurveda_', 'gangnam_nadiayoga', 'bonarich212', 'hearty.lifestyle', 'sinae.jung.7', 'sojung_kim_', 'wildergmq.angela', 'oceanpacific_official', 'mirisu_', 'letape.korea', 'juarezlhi.darla', 'jihee____', 'han_ungi', 'vvljn____', 'rxorn3x', 'oo2.12oo', 'jo_yoonseo_', 'xuxunx', 'seo_young_h', 'rainmaker_0622', 'hee_hee_chu', 'choijk2690', '911111hana', '2._j0', 'jywsj', 'ax._.milk', 'leexeoin', 'jxxyul', 'ennn__00', 'berry_vely_s2', '_96.s2', 'googlewigglegoggle', 'boy2on', 'yoga.one88', 'shineglam_of', 'january_cui', 'appointment_studio', '_belle_j', 'yogiyogibo', 'sooooolbit', 'potaro_hibinokiroku', 'pado_so_ri', 'move.kdh', 'ji_minns_', 'h_jung2_4', 'b2.my___yezy', '_n.rae', '_gelucke8om_', 'yogaseom', 'vitaminamina.gram', 'theintrovertsyoga', 'theclassicpilates', 'tan__zzang', 'susanhchong', 's2soy_', 'numinousyoga', 'nametag_design', 'mingzi552', 'kyliekpyoga', 'im_ggum', 'dave_yogastudio', 'bit_na._.j', 'artsyoginista', 'ado_m1n.g', '_e_ghaempanah_', '_daon_yun_', 'yogini_vanessa_', 'l3na.kim', 'healthboygym_sinbu', '100_kg___', 'yoga_chiangmai', 'yomdy_healthy', 'yogi_0416', 'yogasnowboarder', 'yoga_jeong', 'xodoa4931', 'uotds4831', 'uiope3781', 'uiopr4831', 'tps2740', 'toroe3712', 'too_too_lovely', 'the_heart_trainer', 't.black_cat', 'sunshine_hy_', 'sunshinebungee', 'staryoga_jian', 'ssangdo_nam', 'sophie_seoul_yoga', 'soop_foret', 'smtiger_gym_', 'smk_dancewear_kr', 'sjpqezov851887', 'shuuvayu', 'seven.seasworld', 'shareyoga_su', 'sayu_yoga06', 'sansojiwon', 's1o._3', 'resortlab', 'practicingyoga', 'plates._.mk', 'pilaroum', 'piggie_sh', 'only_joaa', 'o2healgarden', 'natsuki_trsw', 'natalya.levenets', 'momoj_dress_shop', 'merci_yoga_', 'mayomooni', 'mcleanfor.gabriela', 'man._.dooo', 'liyong_golf', 'lilyandgiru', 'lini_andyou_3', 'lady_lara_0201', 'kirin.shoes', 'kim_hyeyun2225', 'kangs_note', 'juju__kim', 'journey__2', 'jinyoung_gram_', 'jejuspinning', 'j_mean816', 'j.utopiaa', 'hongseongho493', 'heartfulness_hana', 'healthboygym_sinbu', 'hamtori_13', 'gr2shmd', 'fodos7890', 'flora__bonnie_', 'dosoa3821', 'dayayoga_studio', 'daheechoi_', 'crossfit_dong_dong', 'climbawaykay', 'cind.yoga', 'chs.dht', 'choijeesoo_', 'chjj818', 'chichang43', 'ca_niss', 'body_channel13', 'beyoum_jiminyeo', 'bettervely__', 'beaver_0815', 'bbopole', 'be_um_yoga', 'bb_pilayo', 'bayo_yoga_', 'ashylist_studio', 'anyunheeyoga_pilates', 'aosie3721', '_ya_89', '_love.of.fate', '_f.soeun', '5second_da', '41.0mn', '_suuhyun', 'suziooi', 'princess_ana_liz_official', 'yunseo_studio', 'yong_yong.e', 'yogini__hyuna', 'yoga__yeona', 'yewon___0830', 'yantisong123', 'xa1_health', 'vonamyo', 'viiinnnnnnnn', 'tlguss_02', 'tlight_2g0_', 'taoyoga_saerom2', 'susuyoga_', 'suziooi', 'suhakuyoga', 'studio__cuba', 'soru_____', 'shauntareny', 'see_hyoung', 'saya_yoga.222', 'sang__illll', 'samboogi', 'r1m.o1', 'pila_yogini', 'parkyonghyun77', 'p_draw___', 'p_y_society_cheomdan', 'p_log100', 'on_yogastudio', 'min.gyu7938', 'mi_yoga00', 'mi_so.song', 'lo_reve_design', 'lixm_fit', 'kbom__2.2', 'jungminby', 'jstar.fitness', 'jonggak_ypilatesnyoga', 'jjjjaaaaeeeee', 'jinhaepilates', 'jihye_19_5', 'jee_925', 'jae.yoga.pilates', 'iooi__j', 'imayogihk', 'hoho.plus', 'hj__young', 'hanayxj', 'hamg_project', 'h0lizy', 'gamja__c', 'gabayoga_kr', 'foundy.me', 'flyingyogigi', 'develop_rianhj', 'ddouble116', 'dagym_yoo', 'cracker_______', 'cho_sung_ju', 'casam010', 'byul_.dove', 'bong9_j', 'bodycontrol_training', 'bingsoobin9_', 'aude_yoga', 'a_minacle', '2_0518', 'basic_lesson', 'zingong_yong', 'zelda_park', 'you_zin', 'yogadana_fit', 'yogi_seoul', 'yoga_jessica_', 'ye._.won._.s', 'y.u.u.j', 'wayto.om', 'vividahro', 'twin.su', 'suzyinyoga', 'sunsetszin', 'sujannee', 'stella.hanbuyl', 'ssonghhaa', 'showfit_photography', 'seul.___.gi_', 'serene_serenity', 'ruciel_mall_5570', 'ram___zzi', 'raan_yoga_pilates0410', 'quickreview7', 'pole_jiya', 'pilatesh_jenny', 'pinkhara9', 'pearyyoga', 'onsaelove', 'nunnunannaa', 'nooo_dumbbell', 'nextfitness_seok', 'merry_yoga_', 'mandoo._.river', 'labeaute_mor', 'l_ch77', 'kongeungkyung', 'ko_ko_workout', 'khulan__________', 'k.kyu_0715', 'jung_.potato', 'joo___h94', 'ji_n_n0', 'j.jyr__', 'i_park.commu', 'herejisoois', 'hee_s_new_s', 'haejin__', 'gyeol.draweat', 'gpdnjs_91', 'freediver_bbotamin', 'fit.adrop', 'esperlmall2', 'diptir_yoga', 'danbusa_sava', 'coach.mino', 'cldud1234', 'choichanheekr', 'choichanhee.kr', 'bodynsol_sd', 'bo_k._.y', 'beaumondepepe', 'barasona_coffee_bakery_yoga', 'backpack_of_artist', 'ajna_inyoung', '__the.reve', '7_9_63__', 'uki12318', 'zkzkzlzlzizi', 'zieunyoga', 'yujin.pilates', 'yoga_lyn_', 'yogajini_draw', 'yoga_yeonju', 'yeonjung1575', 'yejimon.0_0.s', 'w0_n__', 'today.tomorrow.for.us', 'sun_vely29', 'shine_ayurveda', 's__keun_', 's2.y__6', 'ruhen_yoga.pilates', 'roum_yogapilates5', 'rewater4me', 'reboooting_homt', 'pye__yep', 'plus_7200', 'pilatesori_', 'paty0418', 'p.p.e.m', 'ol__may', 'nini__s2_', 'nataraja_ek', 'nalyo_bonnyfit_ss', 'min_mma02', 'min.d_yoga', 'luv__cream', 'luv.my_body', 'lsuhahl', 'loel.u', 'llla_goodmorning', 'kori_liuwa', 'kikikisuinisuic', 'khj_153', 'k._.nnani', 'jw0ne1004', 'judocrossfit', 'jodeodeok', 'jjeong2__', 'jjcol_d', 'jj_ell_y', 'jayge.bro_offcial', 'irai_yoga', 'i__end.wl_', 'i.mdust', 'hyunju_95', 'hyeonii_s', 'honja_homt', 'hodie_kr', 'hihula275', 'ganji_diet', 'g0220_g', 'flowermin_01', 'filmvictor', 'fashion_198204', 'diego_wave_yogi', 'ddu___bi', 'ddong_ggo_mong', 'daom_changwon', 'danahotyoga_816', 'd.hye0', 'd.__.hxxn', 'cuiryeong', 'choij.ye', 'chang._.55s', 'ch_xng', 'celine__lim_', 'ch.seol', 'casino_vip_model', 'bondy_yoga_pilates', 'bodychannel.__.ht', 'bigtree_tattoo', 'big_dong_2_', 'b0rm_', 'ayurveda_yoga_kr', 'arnayoga_jh', 'ahepf79', 'agni_yoga_pilates3', 'actingcoach_jung', 'a.yu_xx', '_changjae_', '__fitness_99_spaseoul_eden', '92brianna_cho', '3.l7kg', '2loui_s', 'ye_ri_ming', 'yogabeot__', 'su.jin0223', 'yoon_hyung_jun', 'yln__o', 'yoga_i.ge', 'yogasis_official', 'yogafulnesslife', 'x_xxey_', 'wonyoga.pilates', 'westglass_', 'theshotyoga', 'teong12', 'tattooing_nature', 'sosohan_yoga', 'sooborru.yoga', 'shes_yoga', 'seul_gi0620', 'sbodyfit_yangju', 'sadhguru.hangeul', 'rattan_always', 'raku___uu', 'rabbit_jjhh', 'r_ddung', 'r.kdb.s0', 'planbfitness2', 'pilates.chae', 'pilaby.youngshin', 'owenhab.earnestine']
    user_infos_list = user_infos_list[110:]
    ##2. 유저 분할
    total_user_infos_group = divide_user_infos_list(user_infos_list, group_size=1)

    ##3. db 발송
    send_total_message(total_user_infos_group, text, project_name=project)
