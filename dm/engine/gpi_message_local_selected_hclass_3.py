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
from instagrapi.exceptions import UserNotFound
from db import m_instagram
from dm.engine import completed_target_influencer
from dm.engine.exceptions import *
from dm.execute.run_select_influencer import get_influnecer_info_by_project, search_influencer_info, \
    get_influnecer_user_id_by_project
from dm.prepare import get_dm_source, get_influencer

FORMAT = '%(module)s.%(funcName)s - %(message)s - %(levelname)s - %(asctime)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)
if logger.hasHandlers():
    # Logger is already configured, remove all handlers
    logger.handlers = []
logger.setLevel(logging.INFO)

# host, port, proxy_username, proxy_password = "mobile.ipb.cloud", "7777", "customer-fydh21628401-asn-20057-sessid-RcPU-sesstime-30", "awR4Sad2t"
# host, port, proxy_username, proxy_password = "resi3.ipb.cloud", "9000", "MrIlCvzYImHc0I3t", "wifi;us;;;;"
# host, port, proxy_username, proxy_password = "resi3.ipb.cloud", "9000", "AX7S3xZk5L9RF1So", "wifi;us;;;;"
host, port, proxy_username, proxy_password = "mobile.ipb.cloud", "7777", "customer-fydh21628401-asn-20057-sessid-RcPU-sesstime-30", "awR4Sad2t"
proxy = f"http://{proxy_username}:{proxy_password}@{host}:{port}"

db_conn = m_instagram.InstaDB().conn
SERVICE_INSTAGRAM = m_instagram.InstaDB(db_name="service_instagram").db
INSTA_ACCOUNT_OBJ = m_instagram.InstaAccount(channel_name="instagram")
INSTA_ACCOUNT_OBJ.client_name = "admin_test"
USER_CHECKPOINT = SERVICE_INSTAGRAM["user_checkpoint"]
ITEM_USER_COLLECTION = SERVICE_INSTAGRAM["user"]

max_login_try_num = 2
max_messages_per_day = 100
max_group_size = 30
client = Client()
client.set_proxy(dsn=proxy)
check_valid_user = True
def read():
    user_list = """"""
def select_user(username=None, client_name=None, max_messages_per_day=None):
    account_setting_info = INSTA_ACCOUNT_OBJ.select_and_update_user(username=username,client_name=client_name)
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
def get_user_id_by_db(username):
    doc = USER_CHECKPOINT.find_one({"username": username})
    return doc["userid"]

def get_user_id_by_username(username):
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
    id = json_data["data"]["user"]["id"]
    return id

def infinite_login(username,max_messages_per_day, client_name=None, session_id=None):
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
    response = client.user_info_v1(user_id=userid)

    return int(response.pk)

def get_valid_user_names(user_name_list):
    valid_user_names = []
    for username in user_name_list:
        try:
            valid_user_name = get_user_id_by_db(username)
        except Exception as e:
            logger.warning(f"{e}//user_id-{username} is not valid_username,{e.__class__.__name__}")
            if e.__class__.__name__ == UserNotFound.__name__:
                ITEM_USER_COLLECTION.delete_many(filter={"$or": [{"username": str(username)}]})
                USER_CHECKPOINT.delete_many(filter={"$or": [{"username": str(username)}]})
            continue
        else:
            valid_user_names.append(valid_user_name)
    # user_ids = list(filter(lambda x: get_user_by_id_lamadava(x), user_ids))
    # user_ids = list(filter(lambda x: x is not None, user_ids))
    return valid_user_names


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


    user_ids = get_valid_user_names(user_name_list=user_infos)

    ###dummy
    # user_ids = []
    # user_ids.append(33873703194)

    logger.info(f"get_valid_user_names:{user_ids}")

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
            logger.error(f"response 타입 에러:{e.__class__.__name__},{e}")
            request_retry_num += 1
            ### request 가 max retry 를 초과했을 때 다른 아이디로 로그인 해준다. request_retry_num -> 0 , account_retry_num += 1
            if request_retry_num >= max_request_retry_num:
                logger.error(f"client error:{e}, retry login //request 횟수 초과({request_retry_num}) 다른아이디로 로그인 해줍니다. // account_retry_num :{account_retry_num}")
                request_retry_num = 0
                account_retry_num += 1
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

        if count_send_message != 0 and count_send_message%500==0:

            logger.info(f"쉽니다 10분")
            time.sleep(600)
            pass

        target_user_infos = total_user_infos_group.pop(0)
        logger.info(f"target_user_infos:{target_user_infos}")

        try:
            next_account_info = send_message(user_infos=target_user_infos, text=text,
                                             next_account_info=next_account_info, project_name=project_name)
            count_send_message+=1
        except Exception as e:
            if e.__class__.__name__ == AccountException.__name__:
                logger.error(f"{e.__class__.__name__}")
                logger.error(f"simal")
                return
            if e.__class__.__name__ == AccountRetryExcessException.__name__:
                logger.error(f"{e.__class__.__name__}")
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
    project = "hclass_type_3"

    ##파일이름
    filename = "hclass_type_3"
    project_start_date = "2022-10-07"

    text = get_dm_source.get_source_message(f"{project}.txt")
    # user_infos_list = user_split(""" """)
    user_infos_list = ['run._.hyein', 'jooeunzzing', 'mmi0___0', 'eunny._.pila', '_pilatesday', '___syun', 'runlim_2e', 'mingso_exercise_diary', 'nir__yoga', 'yerin_pilates', 'yom__e2', 'ny_day_', 'sudingzelly', 'wxxn_h', 'yoga__sin', 'ggangsso_', 'woojung111', 'mimo._.jin', 'yoon._a71', 'hyuna_orum_yoga_', 'kks_xnn', 'lo__un', 'kyraondamat', 'yoga_trinity', 'gyeongrim9211', 'victor_choii', 'bright__tree', 'yogini_mina', '___yu_j0_0', 'premyoga_gumi', 'syjy9_9', 'hyeshin_ing', '__jjhyeonnn', 'pilates.basic.9', 'prema_seojin', 'lisil_215', 'jin_a_1992', 'pila_gh', 'yoga__jeong', 'eunsaem_yoga_pila', 'h.zizii', 'hereyena', 'ruddlgram', 'princess_or2', 'janelee.yoga', 'sun___im', 'park_yongji_', 'yogini_hyuna', 'yuni__yoga', '__hwa_nee__', 'minagim341', 'january.uu', 'wo_to11', 'studioakion', 'chieyoga_0108', '_starry_summer', 'insujigram', 'arinazakharova478', 'maeumknah', 'movement.on', 'yzgzzz', 'pila_suyeon', 'ong._.pt', 'booyoga', 'mi_body_', 'simyo_ga', 'incellderm_aura', 'lehayeon', 'yoga_ryeong', 'yogaeun_healing', 'kafrehab', 'hazel_v_v_', 'jeong_yoga', 'nikitenkodobrava', 'useungyoga', 'bohee.kim.58', 'merry_yoga_', 'bliss_vimala', 'mina_nalee', 'rufinakovalchuk61', 'sunaeyoga', 'yloo0005', 'seoyu.life', 'xxssseeee', '2seohaeun2', 'kim_yeonheee', 'river__yoga', 'haley_yoga', 'duadlfkd', 'ceonsuyun6', 'nadi_ashtangayoga', 'myojungde_', '___hj.____', 'isabelkwakyoga', 'ennn__00', 'h_jihun', 'y___eunnni', 'song_yi_jung', 'yogini.sue', 'ssu_a_seo', '_yo_qeu___', 'hn_santosha', 'hye_ranyy', 'gigi__yogin', 'jeong_ah_yoga', 'belita_yoga', 'ihyunk', 'jihyuni.yoga', 'kieferella', 'yogini_hyogini', 'yoga_hzz', 'pepper.rainbowls', 'thanq_yoga', 'lesjj7', 'p._.byeoul', 'soyoun1207', 'jeongeun_yoga', 'ji.won.c', 'eunhee.memories', 'damheekk', 'y0rgasm', 'minj__park', 'live__hara', 'yh_yoganeul', 'koosun89', 'merrybandi_', 'hyein_0406', 'jasmin.k.tiger', 'yogaeun__', 'yoga.ondo', 'yoga_yul_99', 'bk_yoga', 'yoga_woogi', 'jy__yoga', 'olor_yoga', 'hum_y0ga', 'sem.ssem', 'yoga_royy', 'naulimyoga', 'ubob.eee', 'cheers_enzo', 'secrets__fit', 'dave_yogastudio', 'iamyogaone', 'yogaroum_star', 'yogapila_hee', 'yoga_hakyung', 'tess_healthy_style', '2_joo_kim', 'soop_foret', 'ignos13', 'wondernails.brilliantyoga', 'luna1213_', 'ha_ppi___', 'csjzzang9246', 'sulkiki88', '_u_riii', 'pila_luv', 'nirodha_y', 'hyollive', 'ye_explorer', 'hyein_kang90', 'auniii_kwon', 'pushminda', 'exercise_f4j', 'rhythm_snow_', 'imirabel_official', 'pilates_ma', 'wonhee_hong', 'yoga__hanna', '___j.eok', 'mac0020', 'd.derm_', 'ahndahnda', 'aeryeon_yang', 'jieun.yoga', 'springstellas', 'shanti_viator', 'yogini_nana', 'hyojin9234', 'ha_eun_p__', 'on__simm', 'hana_acv', 'ys__lee04', 'dd_____hj', 'ji___yn', 'favor_pure', 'mi_jjjjju', 'mond_pilates', 'siena_hami', 'yejiyoga', 'shin_taeo', 'j.hyo.jeong', 'pila_daily_', 'seul____s2', 'doublej.studio_photo', 'james_song_tk', 'san_____na', 'yuun___m', 'jjing.fit', 'khjyoga', '__eun__o.o', 'aircanada_sun', '__hyun_k__', 'andus_official', 'seon_mi__', 'shonheejoung', 'anyoneyogamadu', 'youn_pilates', 'j._.young_e', 'g_neei', 'seungmozzi_yogi', 'just_hyojin', '4_4_esther', 'yoga1127', 'ivypilates_hh', 'suheartyoga', 's____s_love', 'vivid_chung', 'the_weeeek', '_xxngxxn', 'im_jiw', 'c_h_21_2', 'yoga_hana.k', 'chunsia', 'hennie_al', 'siwa_yoon', 'lizzy.doit', 'hyep__.__', 'solyyyy_', 's__ung.e', 'haho_haaahooo_o', 'jisu_like', 'eu____b', 'diet_hye65', 'nuskin_bigstory', 'bodyfit_yul', 'yang_songhee_', 'kang_16.04.12', 'jami.zip', '810521sun', 'borabora_1105', 'bonbonbubble_', 'ryeoeun.kwon', 'youyon___', 'pila.jian', 'soy_onadiet', 'bini__potato_mom', 'oh_a.sis', 'hyelin_yoga', 'aitchxh', 'rom__romrom', 'varunayoga1004', 'kkkcare', 'chaem.co.kr', 'lolhana1231', 'yooooooooom_', 'move_ms222', 'n.aelii', 'saena_163', 'jiah_0527', 'alphapurple', 'u_uri__', 'piline_hy', 'mmichelin_diet', '2ogram', '__a_yeon', 'so___ri_', 'steady_hun_', 'basic_pt_studi0', 'seong2un', 'haranxs', 'k_yeonju_', 'artistmimicha', '29flower30', 'yogavna_vayu', 'beomq_building', 'yoganamu_momo', 'ra_ni_star', 'namaskar_restaurant', '1limjungsun', 'ayurgong', 'jisun.ardor', 'dieter.dh', 'yoga_appletree', 'han_yujin88', 'artlovervanrijn', 'yoga_momam', '__yh424', 'pinnnymph', 'yuhyel_', 'atti____j', 'seyeon6711', 'kkommizi', 'hyen___k_', 'hong.ssseung', 'yogi_hyonii', 'yi_seul92', 'yogaon_zen', 'yeon2vely', 'y.b_jjung', 'xixixixiri', 'west_delay', 'selena_kang_', 'rvd_fit', 'rlo_or_jo', 'qo_op____', 'pd__pi', 'me_florette', 'maryss_93_', 'lucky_haejin', 'josu_hyeoun', 'i.seungah.you', 'gy_1201_', 'demi.in.sydney', 'aa.___.ra', '_._.oo_o', '28balance.workout', 'yogihihi_', 'rainbow.lts', 'jieun.yogalife', 'sivanandayoga_hannam', 'sara.flower.yoga', 'mans_fits', 'kimssun01', 'commonstudio_kr', 'suhyeon.love', 'shinse_yoga', '3.26_hg', 'choichamp.numik', 'sodamyoga_online', 'gangnam_nadiayoga', 'bonarich212', 'hearty.lifestyle', 'sojung_kim_', 'mirisu_', 'jihee____', 'rxorn3x', 'xuxunx', 'hee_hee_chu', 'ax._.milk', 'leexeoin', 'ennn__00', '_96.s2', 'boy2on', '_belle_j', 'potaro_hibinokiroku', 'pado_so_ri', 'ji_minns_', 'h_jung2_4', '_n.rae', 'tan__zzang', 'susanhchong', 's2soy_', 'mingzi552', 'im_ggum', 'dave_yogastudio', 'bit_na._.j', '_e_ghaempanah_', '_daon_yun_', 'yoga_chiangmai', 'yogi_0416', 'yogasnowboarder', 'yoga_jeong', 'tps2740', 't.black_cat', 'sunshine_hy_', 'sunshinebungee', 'soop_foret', 'smtiger_gym_', 'smk_dancewear_kr', 'seven.seasworld', 's1o._3', 'piggie_sh', 'natsuki_trsw', 'natalya.levenets', 'merci_yoga_', 'mayomooni', 'man._.dooo', 'liyong_golf', 'lilyandgiru', 'lady_lara_0201', 'kim_hyeyun2225', 'journey__2', 'heartfulness_hana', 'hamtori_13', 'gr2shmd', 'flora__bonnie_', 'daheechoi_', 'choijeesoo_', 'cannitationyoga', 'body_channel13', 'bettervely__', 'beaver_0815', 'be_um_yoga', 'bayo_yoga_', '41.0mn', '_suuhyun', 'yoga__yeona', 'yewon___0830', 'yantisong123', 'xa1_health', 'tlight_2g0_', 'studio__cuba', 'soru_____', 'see_hyoung', 'saya_yoga.222', 'r1m.o1', 'p_y_society_cheomdan', 'lixm_fit', 'kbom__2.2', 'jstar.fitness', 'jonggak_ypilatesnyoga', 'jihye_19_5', 'iooi__j', 'hj__young', 'gabayoga_kr', 'develop_rianhj', 'ddouble116', 'cracker_______', 'casam010', 'byul_.dove', 'bodycontrol_training', 'bingsoobin9_', 'aude_yoga', 'zingong_yong', 'you_zin', 'yogadana_fit', 'ye._.won._.s', 'vividahro', 'sujannee', 'stella.hanbuyl', 'ssonghhaa', 'showfit_photography', 'seul.___.gi_', 'quickreview7', 'pilatesh_jenny', 'pearyyoga', 'onsaelove', 'nextfitness_seok', 'merry_yoga_', 'ko_ko_workout', 'khulan__________', 'k.kyu_0715', 'ji_n_n0', 'i_park.commu', 'haejin__', 'diptir_yoga', 'choichanheekr', 'choichanhee.kr', 'ceoom', 'bo_k._.y', 'beaumondepepe', 'barasona_coffee_bakery_yoga', 'backpack_of_artist', 'ajna_inyoung', '__the.reve', '7_9_63__', 'uki12318', 'zieunyoga', 'yoga_lyn_', 'yejimon.0_0.s', 'w0_n__', 's__keun_', 'rewater4me', 'pye__yep', 'plus_7200', 'paty0418', 'nalyo_bonnyfit_ss', 'luv.my_body', 'loel.u', 'kikikisuinisuic', 'judocrossfit', 'jjeong2__', 'jjcol_d', 'i.mdust', 'hyunju_95', 'honja_homt', 'ganji_diet', 'diego_wave_yogi', 'ddu___bi', 'ddong_ggo_mong', 'danahotyoga_816', 'd.hye0', 'cuiryeong', 'chang._.55s', 'ch_xng', 'bigtree_tattoo', 'ayurveda_yoga_kr', 'arnayoga_jh', 'agni_yoga_pilates3', 'actingcoach_jung', 'a.yu_xx', '3.l7kg', 'ye_ri_ming', 'yoon_hyung_jun', 'yoga_i.ge', 'yogasis_official', 'yogafulnesslife', 'y_u_n_j_e_o_n_g', 'x_xxey_', 'westglass_', 'sooborru.yoga', 'rattan_always', 'r_ddung', 'pilates.chae', 'ollot_official', 'nalyo_js', 'minayogagraphie', 'lylical_makeup', 'k___minseo', 'jyoga_pilates', 'juuuuuuvely', 'jeong_na_won', 'j_eongyeom', 'imdundoo', 'hur.eun.dong', 'h._jin.et', 'godyou_u', 'cha_chabling', 'cat.siru', 'b2positiv', 'ay._.jeon__', '___s.mn', 'angmin_gym', 'zzym_e', 'ululuyoga_sunae', 'team_masean', 'suhotyoga', 'rightiger', 'purecoconutwater', 'noyh.oz', 'nah_hyun_jung_', 'minyi.yun', 'luv_yu_s2', 'little_house_of_yoga', 'letsdoyogakatherine', 'kimkkomida', 'jane.jieun.lee', 'hyooo__ni', 'haom_daily', 'h0ngxy', 'enjoykorea.asia', 'e99ran4', 'danielle.yoga_', 'cdouro_seoul', 'bodynsol_dp', 'binu_t.t', '___hj.____', '176__73', 'zuzu_gadak', 'team_big_iron', 'zza_i', 'yupilates1', 'yomi_ria', 'yoga__forest', 'yogaleehe', 'vtm_yogapilates', 'u_eimi', 'the._.one._.pilates', 'su_yogaroom', 'shinkijeong', 'seulkummm', 'sanhwa.choi', 'probusmat', 'pjbinnn', 'oov_babe', 'myown_sequence', 'midnightblanc_workout', 'metime_7777777', 'lsh.mom', 'lee__yun_2', 'juyoung218', 'jinmimo_vement', 'jijieunji', 'jeonghyunjeong', 'hyesinyoga', 'hongchae_h', 'heyan.sw', 'hanwol_07', 'gr8_zzohya', 'g_neei', 'com.plex87', 'bandiyoga', 'amonxlisa', 'abos_fitness', '_lovely._.lee_', '__naeun02_06', '9.5_jw', '2st_body', '2_ppeuda', 'ayeong_diet0_0', 'be_halcy.on', 'yogainstructor_lisa', 'yoga_coffee.kiwi', 'yoli_graphics', 'yoga_wonderland', 'yogasthiti', 'winswinn', 'vacatioplace', 'tumsehee', 'su_166m', 'stretchinghannah', 'sashapoledance', 'ppeuisfu_n', 'prem__chungdang', 'parkfitseoul', 'o._.oeeee', 'namaste_hyun', 'lenayogapilates', 'koko_eun', 'kits_miy', 'karateseoul', 'keti.kay_', 'k_y_jin', 'jini_pila', 'hwartist_museum', 'hongsilly', 'haemil_yogapila', 'gaeul_snpe', 'flyogaying', 'fitk1m', 'elf____yoon', 'ddine_u', 'dan12340099', 'chae_sunbi', 'breathe.in.yoga', 'aracel1_k26', 'ajnayoga_hongdae', 'about__chuuu__', 'abel.pilates', '_y_y_2e', '_s.water', '_euniroom', '9ooju_0', '729hj_', '172.93.01.14', 'zestpilates_drc', 'yyj.photo', 'yogasoop_studio', 'yogafield_jn', 'yogabyotters', 'willbe.yora', 'vvoowv', 'tpz_pilates', 'taoyoga_gongju', 'supia_studio', 'su_nah_', 'soyeonn___', 'soonsooyoga', 'sin_uk_jin_', 'seonhyelsh', 'reesnhae', 'pole._.02', 'pilates_youri', 'nana__company', 'mj_onyogapilates', 'mizuki_easyoga', 'mixtout_atelier', 'min_.__._ji', 'lyrical_body', 'loveyogavid', 'lala.layoga', 'lacyjoellyn', 'kyungsannn', 'jjumjjumabba', 'jiyiyoga', 'jiweon9113', 'jian_yoga', 'ji_e0323', 'jeonggug1285', 'jejuyogahouse', 'jang_moonsun_', 'ines.lee.ee', 'i_b_rami', 'i.luv.emily', 'hyosun_petrichor', 'hyesin', 'guri_bnb_yoga', 'gnsportsclub', 'dybodylab', 'designstudio__j', 'czzji', 'chenyao321', 'by__yul.2', 'bbostagram_', 'balletically_offical_', 'ariayogapilates', '_syun_i', '__jymoon', '940617__', '4yoga_yjyj', 'jjanieeee', 'shin.eb', 'mayday3131', 'yuha331', 'youngsclub1090', 'yogawjen', 'yoga_sakiokamoto', 'yogini_bella', 'yogaon_studio', 'yogini_neul', 'yogini_changhee', 'yogaonyou', 'yoga_rally', 'ye_riniin', 'xiusfitness_siri', 'verna_guo_pilates', 'tattooist_shinji', 'sun_bird90', 'stars_mirim', 'sol.x__', 'slowslow_giri', 'skyyogakula_gildong', 'skyeeyogi', 'sindy_yoo', 'seoheehaan', 'seasylove', 's_u_jinn', 'poppin_kmoon', 'pila_ho057', 'picaso_lee', 'park_byeoul', 'paixintr', 'omoyoga_13', 'ohboo.workout', 'nla_workout', 'njyouth1939', 'nakigrim', 'mts_korea', 'mirinda160', 'miyeon_070320', 'mindfitness_ulsansongjeong', 'mi_ye0ng_', 'lo_____ra', 'livin_hanok', 'kiwa_012', 'khj8658', 'kash_to_shine', 'ju___hee95', 'jongno_gumin', 'ha_sungu', 'gomgom_yeseul', 'fsyoga29', 'forfree_sy', 'fobene_sport', 'evieyoga', 'eimi_shanti.grace', 'earthy_yoga', 'doldole_cat', 'dareumyoga', 'daomplates_therapywallyoga', 'dagamsumin0904', 'bodynmind_profile', 'bomeunkimm', 'bjun_2', 'bareugeyoga', 'barada4452', 'banchikini', 'baekhayan', 'b.s_writer', 'ayabe_non_', 'anahatakorea', 'americayoga_gongdeok', 'abelpilates_5', '_kimsorim', '9v9ryday', '5.00am_._', '20081127_donghae', '2.27_jy', 'belle__mee', 'zzonddo', 'yuuush_', 'yuzitheyogi', 'yumi_pres.yoga', 'yujinfly0212', 'yoxa_eun_ixht', 'yoga_route', 'yogag_studio', 'yogachoi_mia', 'yoga_sol.x', 'y2gym', 'wwwlucokr', 'woosung_24', 'vip.yogapilates.buk', 'tomomi_yoga', 'thestarfit_pila', 'thejiyoonson', 'theflowroomyoga', 'tangyudance', 'sun.angella', 'sujin.yoga', 'suj5422', 'su__log__', 'sssssmii', 'sso_erum', 'soum_yoga', 'soo.j1222', 'sol.sportwear', 'somsom_1224', 'shanayoga_', 'seojeong1101', 'seaweediskim', 's.won_a', 'ryan__bee', 's.yoga_', 'runningyogi_sona', 'riyonyoga', 'redboxingclub', 'propps_official', 'prem__studio', 'prita.20', 'pilates_enzzi', 'pila_uy_', 'pingguruu', 'peaceandu2', 'nycottonclub', 'mishu.mishu', 'miku__1222', 'mahoyoga_lava', 'loveyour_choice', 'lims_yoga', 'leegeonn_', 'lee_uj_3164', 'kwon_1105', 'karinporinky', 'kayo_mishima', 'jiminyoga', 'jim._.in00', 'jf_georgeee', 'jahayoga.lab', 'j._.y_a', 'incense_book', 'ideakorea_official', 'hyebinidaa', 'hun.hun126', 'hongsi._.diet', 'hoker_bell', 'heojae_', 'goodlife2886', 'glet_k', 'ggomvely_ji', 'eastyoga.movement', 'ddw0902', 'darak_kim', 'daon_pilates_', 'dam._.daa', 'dallasgym_dalma', 'coserygangnam', 'choissun_', 'cheonan_sisul', 'cha.fall', 'bhati_yoga', 'bareun_line', 'barofit9395', 'badaji_17', 'arete_tattoo', 'and.panini', 'americayoga_official', 'aeroportjoga', 'a_meditation_room', '_rlo.kor', '_core_golf', '0vu4me_', 'dieter_172_', 'zayu_za_yu', 'yuni_pilates', 'yunjoy___', 'yogahanayo', 'xmsxsmx', 'vaper_jun', 'tower__pilates', 'tara_yoga1205', 'suzy_.j', 'sun_ny_pilates', 'sinsa_sports', 'shin_boyoung', 'salim_whole', 'sa_ng.hee', 's22222222y', 'resortfit_jw', 'pilamingo_', 'paperbakery.co.kr', 'oxx_ri', 'o.n.l.d.o_pilates', 'nana_2752', 'namurogrida', 'namuyoga_studio', 'moony__fit', 'mellowww_okr', 'm.e.pilates', 'lovelsy0815', 'lim_sso_young', 'ke_beii', 'k._.821', 'july07_life', 'josungjung_', 'joyful___s', 'jaeti01', 'inomis_clothing', 'iamuwoo', 'iam4da9', 'haneul_haneul____', 'eunjalee_', 'engbbubbi', 'doid_ksh', 'diet.on__y__', 'danji0313', 'co.ppo', 'choco_mi__', 'boyeon08', 'borammmiii', 'audrey_jewelry__', 'aria_official_sg', '_dew_drop', '902_s_yoga', '5gguggu__', 'yun__mimi', 'yoga1gii', 'yogaroum_seolhee', 'yoga_sooa', 'yogimin_flying', 'yogini_8181', 'yogais8588_official', 'yeongnani_', 'yagondayoga', 'wolfenrm.marci', 'uyu_ragdoll', 'suuull', 'popsys1', 'onoff.zip', 'moreout_korea', 'moonflying_yoga', 'missj1227', 'minji_matilda', 'ming._.0210', 'lovelovelove0_0', 'line5434455', 'laonking21', 'lamoda__jinny', 'kongs_ss', 'krdha77', 'juuuuu_vely', 'joeun_flyingyoga', 'jjeonghee78', 'jj__training', 'jigeuiyoga', 'j.chu__yoga', 'its_gym_sungbong', 'ireh.pilates', 'inyogapilates', 'ilsan_ashtanga', 'ibro_travel', 'i_lovethisone', 'hyunas2', 'hyul_study_official', 'hun2_87', 'healthy_jigu', 'happiness2roro', 'hanuva_workout', 'gimyohan2006', 'g.travelersplatform', 'dasom3297', 'blond_saram', 'blueberry.outfit', 'bhavantu.co.kr', 'bboo_fit', 'bab_puul_e', 'apple._.song', 'ann_chant', 'and_spring_feelscrap', 'angela__flow', 'anahata_yoga_jecheon', 'anahatayoga_house', 'an_zung', '_yogini_jiny', '_atclaire', '__breathe_yoga', 'showry__', 'moonppower_', '_jun_yoga', 'yum_eunoia', 'yogaculturalcenter', 'yoloking___777', 'yoga_semi', 'yoganomad_official', 'yoga_jungsan', 'xoyunni', 'xoxomiju', 'workout_sh3', 'wook_tr', 'uddiyanayoga', 'soo_rhythm', 'slowyoga.korea', 'shabang_ggang2', 'shanti_viator', 'rugeoi', 'real.pearl_', 'parkgym_jeong', 'ownaxis', 'open_the_body', 'o3ojju_', 'no.1_mi', 'nalyo_bonnyfit_go', 'nail_ppoya', 'minimi.x.minimi', 'mat.maramari', 'lunayoga_pilates', 'lineholic_', 'laksmiyoga2', 'kyung9_yoga', 'ksy_767676', 'k.8____', 'k_bongdiet', 'jxyoxng', 'juyeonyoga', 'joa__g', 'ji_hye_102', 'imiseon8966', 'im_pilates_flyingyoga_official', 'hyeverystudio', 'hr93.01', 'hola.jaen', 'haewo__n', 'gswoman19', 'g1_yp', 'fresh_young_company', 'fate_healthy', 'enipic', 'ek.779', 'duchesshouse_official', 'dkunstm', 'daaam._.2', 'da_____xye', 'd._.nee_e', 'chxxnne', 'chunsia', 'chj8442', 'atma_yoga_', 'arxxmg', 'andy_raanclassic_pilatesyoga', 'ananta_jieun', 'americayoga_ewha', 'allstarbreakerz_burst', 'after_10y', 'a_ryeong.0325', 'a.cho__m', '_kong_jaban', '__yjin2_', '4.5.0kg', '1yejin2', 'yun_sseul2', 'youngladycoco', 'yoosual_kr', 'yogasadhana_seoul', 'yogahaven.kr', 'yoga.zen.ep', 'yogiuun', 'yogaste_bupyeong', 'yogakaruna2020', 'yi.an.na', 'wlffj2011', 'wannabna', 'useungyoga', 'uo_on_flying', 'today_is_haru_', 'taoyoga_jinju', 'teambenefit77', 'sz_pil', 'sson0303', 'solyyyy_', 'sodaaaamm', 'sm_tiger', 'seronstudio10', 'rrda_yogini', 'rolled_paint', 'redjean_master', 'ranheetanabe', 'priya__om', 'prisha_yogaro', 'pilates365ss', 'ohseongeun0525', 'mong.kei', 'mina__9093', 'mindgroundkorea', 'mariakimluxfit', 'main061000', 'luvin_victoria', 'lovely_zass', 'lina_chupark', 'leeju_youn', 'lee_so_myung_', 'kyeong_na_', 'kmyoil', 'kimgain5308', 'jy_soma', 'juyeon_yeosu', 'jimmy55seo', 'jihye_shin_', 'jeongu_bungee', 'in_nerpeace', 'hrtkd_37', 'hodu_marus', 'hhealthiing', 'hatha_jaehun', 'haeun_s2_', 'gool._.s', 'garden.young', 'f_lyoon_jeju', 'favor_pure', 'eunkyung_parkkkk', 'eunjin___vely', 'eun_pilates_', 'eun___ho', 'eseulg', 'eeeun__s', 'daon.pilates', 'daechungsanda', 'cuty_eve', 'chouchoupilates', 'boramiworld', 'bom_bom_44', 'boksilchoi', 'blevstudio', 'bean0505', 'anotherjourney_', 'aerin03010301', 'abc_sally44', '_yogaful', '_jua_iii', '___blackgem', '3260am', '2ee.mi', 'hito_______', 'nana__company', 'zziniya_v', 'yoojelin_hatha', 'yogarang_pilates.kr', 'yogicookjin', 'yoga_theforest_kr', 'yogaforyou_j', 'yeonchu_04', 'won_mikim', 'wisdom_hoi', 'wanggun_7', 'wade_pak', 'varunayoga_official', 'uncle_omg', 'thenamu.ine', 'team__welly', 'taoyoga_doan', 'sweets._kg', 'sso___mn', 'soyoon_pt', 'slovetoo', 'shaotang1981', 'seo_lila', 'satyayoga.studio', 'sageun2020', 'run_alvln', 'rkss_3', 're_flying', 'rammi_k.k', 'proudbodymove', 'pluma_office', 'pila_u_ha', 'pinkyui1105', 'park_eunhee_jinn', 'orientalartstudio', 'olivia.k_0118', 'nohsabum', 'nalssin_joy', 'mysorefitness_official', 'mw_lim', 'mira3339999', 'minh_3a', 'miirgnod', 'maeumknah', 'lois_verissimus', 'look_so_goood', 'liijihiin', 'leedongshim', 'kyeongin_h', 'koreasingingbowl', 'kks_xnn', 'joy.0730', 'jin_0__u', 'jia_imagine', 'jeongsh__v', 'jeju_pranayoga', 'irinayoga_', 'ifland_lawkim', 'iamheeseo_', 'hiranya_yoga', 'heeyoung.d', 'hajaehee', 'gogodangtea', 'ggimhyangsug', 'eunsuchai', 'eunju3645']

    ##2. 유저 분할
    total_user_infos_group = divide_user_infos_list(user_infos_list, group_size=1)

    ##3. db 발송
    send_total_message(total_user_infos_group, text, project_name=project)
