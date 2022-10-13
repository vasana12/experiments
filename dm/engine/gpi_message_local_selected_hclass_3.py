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
# host, port, proxy_username, proxy_password = "resi3.ipb.cloud", "9000", "MrIlCvzYImHc0I3t", "wifi;us;;;;"
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
    project = "hclass_woman_3"

    ##파일이름
    filename = "hclass_woman_3"
    project_start_date = "2022-10-13"

    text = get_dm_source.get_source_message(f"{project}.txt")
    # user_infos_list = user_split("""""")
    # print(user_infos_list)
    # input()
    user_infos_list = ['only.hyewon', 'h.sy_0219_', 'teamhon_modernbjj', 'ssing_vely', 'yn___kim_', 'jjyeeee', 'sso._yyy', 'coco_170104', 'studiocou_body', 'mj._gym', '_yeolwoon.ra_', 'yoon.six', 'sion._.climbing', 'hajoy_fit', 'run._.hyein', 'sd_hyeee', 'chaehyun3258', 'joa_yeon_', 'better_than_fitness1', 'gymtime_kr', 'san_ellie', 'hipsubak', 'j_eexee', 'forest_n_i', 'stronghyun2', 'mi_hee1748', 'sxxubi', 'strong_jioi', 'trillion_min_hyuk', 'synthapower', 'easy_table__', 'h_hip_g', 'tnapilates_pangyo', 'nail_de_choi_', 'tanz_fitness_', 'anhyijeong5076', 'rohao___mens', 'health_tagram_03', 'show_me_712', 'chloe19890309', '_hyounj', '93idaily', 'bible___kim', 'diet__rina', 'eyemebeauty', 'h.su_zin', 'kim_news_d.d', 'workoutsparrow', 'judol7587', 'bachamelie', '68year_monkey', 'move_ham', 'angelraa___', '930416', 'jooyaa_s2_', 'e3u6n._', 'bomb_j.workout', 'maeng_mons', 'vivizzzang', '162.49', 'silversoo', 'mnm_fc', 'bbom_v', 'jishu_fit', 'daily_jiujitsu0116', 'e_e.seul', 'yunho.jeon', 'parkyoungran82', '__health.soo', 'xxe_168', 'eu_na_1004', 'kh_jiuth', 'da.hye___lee', 'nicechoi_ce', 'sinsofshin', 'hyejeongday', 'z.silver', 'ji_0s_', 'mxxvly__', 'haeri__ing', 'winsome_pilanfit', 'acdongi7', 'a.rinmultishop', 'honey_beeeees', 'rider_do.o', 'laurie_roseday', 'helen_jinhee', 'min_seo_hee', 'gymmood_bucheon', 'chagym_ssu', 'won_ba_', 'rapunsu_j', 'ccaggong', 'workout.umji', 'intj_t_jh', '_hyetban', 'hh0.330', 'fit_jjjeee', 'blessing_wfc', 'k.se_lin', 'daandi.kim', 'differentcompany.official', 'kim_movemove', 'duubuu0__0', 'yoom_snpe', 'new___hotplace', 'daily_workout_lovelyju', 'w1n._.ter', 'workoutgram__', 'sojimeo', 'nandalla_a', 'seoa_jjang', 'go.gomma', '_iamyume', 'upto_crocodile_1', 'jina_diet2021', 'usssss.__.2', 'ji__0106', 'bjjaemin', 'o3o_pila_byuling', 'coolsis.hotgirl', 's_t_ar_98', 'beens_workout', 'bjju._.jj', 'yulia_soyeon', 'mehee.salon', 'i_m_jm_', 'mcfitness_yeonsan', 'hyera.insta.workoutlog', 'mados_sodam', 'studio_rustic_', 'spsa_7', 'realgun_tennislover', 'jin__diet46', '__yoodaeju', 'fit_miji', 'ulsan_nayoon', 'hey_stop_eating', 'kim_recon', '96__05__26', '190_yxxg', 'royalgym_irene', 'mini_zzin', 'hello.young', '_xxmxmxx', 'bunnychaeri', 'run_0508', 'pila_myun', 'soul_pinetree_', 'diary_211115', 'whitegym_8', 'diet_mincho', 'mi.0.gi', 'begsgoat', '175.soofit', 'crimp_yoony', 'diet__cw', 'fox_vintageshop', 'ungkiiiii', 'be_good_body', 'gost_booom2', 'haom_diet', 'did_u_work_out_today', 'yjcorgi', 'workout_chicktaa', 'jyeon2_fit_record', 'che__3', 'ji.__.051004', 'h_ji98', 'upto_dragon_4', 'choifree_', 'my_amy_48', 'clover_hong0402', 'aa_yoon', 'miri___kim93', 'redangel106n', 'choi__hugo', 'g._.eun_e', 'j.be_lovable', 'bbang_y__', 'da_ningo_o', 'choi__yoojin', '051__7', 'dy_workout', 'sang_e89', 'm_minju_', 'shinyoojeong', 'yeun_.y', '000jmmj000', 'baip_0j0', 'workout._.sq', 'dolphiny_o', 'happy.____.diet', 'leeseongchan', 'xy_woojin', 'abdallah.amjid', 'ravi__lash', 'ineffable__j', '2.___s2', 'diet_chei', 'pilatesofme_usan', 'kys361312', 'work_out_hyeonil', 'hyun_vely.__', 'kjfc_15', 'truth_climb', 'hj_teetee', 'eun_ae_company', 'swan______3', 'yoyo_cow', 'clim.mjo_o', 'lv._.moonlight', 'lifelove_s_yj', 'bettermovementlab', '9x956', 'ji__in2', 'leueunsssl', 'hhjj0804', 'this_is.jinstar', 'audgiegee', 'chen_______v', 'yoovely0034', 'nutri_sister', 'e_hye3721', 'nari_0620', 'pinkgabong', 'y2gym_pt', 'zzi__camper', 'h__1379_l', 'mcchowr', 'j.anagram', 'gyminnn_juice', '_yetto', 'be_classy.j', 'hyewon_high1', 'o_1nana_daily', 'healinny_sy', 'manslaipu', '5150_hanna', 'underwatergraphy', 'jw0000000002', 'jooeunzzing', 'bliss.zzini', 'synabro_soonki', 'daily_suuuny', 'bbo_1219', 'janghanna38', 'sssssun1104', 'sin__0913', 'n___hyunwoo', 'la_ven_dia', '20613__jh', 'noopy_yxunx_xu', 'castle._.1_97', 's.e.o.heeya', 'jin_togi93', 'sunday_9.4', 'jpark_diet', 'chae.on', 'hogang_nail', 'yxxnfit', 'seola_lee_', 'runrun_hyojin', 'suneui2257', 'fitboss_jun', 'sara_daily_etc', 'filetmignonn', 'fit_zi.uuuu', 'kilhyunsoo', 'whatsoida.yoga', '_slow_and_grow_', 'miin.__.zu', '_yxxns__', 'oh_hyewon_', 'k1m.mango', '9ucci.life', 'hotzzinie', 'withyeonsu', 'itismelovingme', '94_young_ho', 'slb_jangan', 'julie_snpe', 'bm_weight', 'fit_lyj', 'yun_iia', '99_walk', 'kana_fit3', 'bodysoul_ra', 'min_s_vely_', 'hang.__.iet', 'conorchip_fit', 'muscle_cong', 'lxxso', 'rangpila', 'ez_pharma_j', '03.03_han', 'suzin_cho_wall', 'yo__earth', 'stunningsky_', 'gymmingsunny', '09x01_bom', 'bae_jita', 'clarayoungchoi', 'e.a.t_u', 'd0w00k', 'shinsaida2', 'mo._.170', 'choichoi_table', 'chuuchu_chu', '91_hong_eg', 'ssol_0923', 'yeoun7777', 'rpdudnf', '_10000_gi_', 'jin.young_kim_', 'choi_muscle_memory', 'health_yeonse', 'lee_sun_ha_', 'jaek_93', 'team.ing_somi', 'comoongchi', 'hello_hye_in_body', 'sens_ran2_v', 't_iger_jun', 'y_mi_so', 'genkihealthychaelin', 'kang.mj_frame', 'chief.soyeon', 'woojeong.k', 'sw___im', 'minha0505', 'fitness055_jinhae', '_dorothy_2022', 'nx.yxn_', 'strong_g.s', 'merry.b_waxing', 'soh.ealthy', 's0ngsta', 'jang_yu_lim', 'jungu_cci', '1992.12.11', 'nelli_ppak', 'sumtofu._.diet._.diary', 'dobbyuno_98', 'uuuuuu_seon', 'ariginine', 'high_uzin', '__1013s__', 'hoiz_za7', 'rara.xixi', '66challenge_geon', 'dal.sora', 'h___ryan', 'bo._.kyung_', 'hijeni555', 'tennis_jini', 'hwwwan___', 'jinah_et', 'min____gg', 'heejinny_workout', 'xuxdddu', 'wanwoo_k', 'dillissom', 'ha.yoon_xx', 'yella.j_', 'dear_shini', 'yellni___', 'luv_ssuu', 'hiip_bee', 'lovely._.s00', 'gyeong_health', 'leila.taco', 'groomingi', '_kkyuu_', 'dbwmls', 'jnneev', 'fitin_hun', 'yo2do_eva', 'want.yeon', '365sunny_87', 'hyein4248', 'mo_hs92', 'u__daengfit', 'jisang31', 'hwangzin2', '_rimdingdong_', 'lovesun_916', 'moongchi_dh', 'lovely_grace.l', 'bu_myeon_kim', 'jmfit_mj', 'ssong1577', 'sim.mi', 'maodoyo', 'x13.80x', 'suuuuuuubzzi_workout', 'jini__0227', 'im_your_summer', 'holo_0_life', 'gyoung_run', 'super__dva', 'clair_jeong', 'half.moon.fc', '170cm_48kg', 'limprint_', 'manok_202', 'u.__.genie__', 'mi_.n__a', 'j_xxbutt', 'petstylist__peach', 'happyminning', 'hye.run', 'hyunvelyfit', 'run_perkybiny', 'jewelry_j.yewon', 'gold_s_fitness', 'moon_nyang_', 'ace_seoknam', 'eyhnihs_e', 'sunny._.615', 'kleevely_x3', 'justjoy___', 'l05.11', 'billiysoo', 'daily_exercise0610', 'h_junsu_', 'sy_guma0__0v', '_marorun_', 'orr_right', 'dreamandloves', 'y25n._.ni', 'idgg.2021', 'king_yerin', 'forty_healthy', 'banyooooo', 'wavy_nubes', 'chogunyoung_', 'vegebuilding', 'katrin.yunjin', 'go4it_uk93', 'pilate__ssu_', 'stars_mika', 'help_yun97', 'yu_k_diet', 'lilycoco__', 'yeorifit', 'kkyo_miiiii', '_j.enn_', 'ricepie._.official', 'miyeon_seol_', 'lje___o', 'senghee0204', '183.gm', '_yeding__', 'mj._.xx1', '_endxand', 'referee_crew', 'daldal_diet', 'kelley_won1', 'oopqwertyui', 'ex_lony.b', 'natural_jeong', 'rani__orchid', 'min_ddooon', 'bobdol2_98', 'workout_ju0', 'hulkwannab', 'galong_lee', 'moon_pilates_', 'ye.bbly', 'kkeu_365', 'jinso_young__', 'jina_sam', 'adorable.ssin', 'mmi0___0', 'withberry.xoxo', 'wzihoonn', '_don0422', '158x48', 'jaygbook', 'yea.ji__', '1003_studios', 'jisuya__badminton', 'jolie0310', 'janet_minjung', 'kim_ju0916', 'sungrok_boxing_gym', '__jjuya__', 'luceat_arbor', 'hyundung__minji', 'jay__fitt', 'oh_banjang', 'seo_ddanddan', 'aarme_workout', 'c__ji_w0n', 'todevelop.lee', 'dietkoong', 'mechul_workout_', 'ye0n61', 'love_jiwon_self', 'hyerijk', 'beloved_bini', 'healbeen_', 'on_.diet', 'matcha_likes_smdl', 'localocal._', 'jun_p562', 'l__d_y___', '0707goood', 'xoxo._.ovo', 'x_x______y', 'tam_yeowoo', 'sj01_08', 'goollim101', 'jmh2001_', 'shura_twins_korea', 'dada__o3o__', 'miixsxx_', 'yang__gaeng_', 'go_rip', 'atseul_', 'hotpapa_homt', 'youjin1018_clclclimb', 'hmmm2612_fit', 'choco_dooly', 'sweatlife_jessi', 'j_ekkkkkkkkkk', 'j.siasia', 'mufffine', 'jinie__vv', 'jmlee9302_wo', 'zzo_ohha', 'wolin._', 'jy___fit', 'aesthetic_ryeong', 's.weat_p', '9_oo_h', 'seo_woo__jin__', 'climb_k0', 'h_h0_bxl_2', 'xuju.p', 'natsuhee', 'malang_sohee', '___jun_9_7', 'meri.me', '_sporty_mama_', 'pila._.hyun', 'skylacho', 'triainagym', 'bak.__.bbyorong', 'woong_vely_', 'j_youn_96', 'haena_9_', 'mn.luv.j', 'eunmi_luvly', 'ootd_jinia', 'roseand._', 'tae.woon.wan', 'scxuak__', 'pyo_heee', 'yoonepoint.t', 'moodman_1', 'algobado._.elin', 'byplanky', 'woongkida', 'i_and_an', '96l20l', 'yoon.asha', 'yong_cruise', 'workouteid', 'veryberrypark', '162.0cc', '31.1k_', 'fit_r99', 'toda_yooo', '63.1_fit', 'miyeon_is', 'fit_hong88', '_ghcks', 'body_vivid', 'dagym_jjjina', 'p_kyungstone', 'greentearum', 'diet_178_jini', '_shao_long_', '_jiddung__', '_hoya_mom_', 'sub____', 'filbody_pilates_pt', 'iam.angela._', 'ungskim', 'twotwo_toon', 'yoo.jeong96', 'healthy.hye__', 'climb_o__o', 'ghyun2_', 'muscle._.december', 'mdpt84', 'xongwane', 'kimjin_5', 'haxjinnn', 'opklnm04', '168____s', 'letsworkoutlin', 'sh_boyyy', 'cycling.s2', 'syrene_official', 'sageleesa', 'joo.s_p.t', 'hcmtt_', 'health_kid22', 'imoc4826', 's_who_oon_s', 'z.xxero', 'el_barbie_05', 'dd.bibii', 'bodys_hodong', 'jiyunir', 'kimmemi_', 'whatever___iwant', 'hs_0223', 'fitgirl__moon', 'diet_beeeeee', '_cuddly._.bear', 'ayeoneeee', 'fit_gahn', 'mi.0___k', 'rnbl___', 'again_april', 'eunny._.pila', 'joo.h_j', 'jinil_89', '____oj', 'goyoull', 'bigsgym_jinju', 'beom.car', 'yunjeong.72211', '_pilatesday', 'suunn__h', 'bagel._.wj', 'p.1107', 'mirei_shinonome', 'donutboy_y', 'gonggam.pt_jin', 'c._won', 'boxingvirus_dongincheon', 'lovely.sonvely', 'jisis_life', 'hwajjong', 'o_o._____11', 'mr_mang2', '0404yes', 'gratia_son', 'adora_bin_', 'yourgym_incheon', 'cherish.__h', 'toughjin02', 'ohttu_move', 'sunny_outside._', 'dear._.y0ung', 'rambo_an', 'wingym', 'pigmong___', '_to.jy', 'hong_930813', 'baek_velyvely', 'joovelyfit', 'glimowgli', 'ballic_9.ms', 'y_u_.y._u', '__sunx', 'bbotle_jun', '3357ae', 'h_yojjjj', '_peachyun._.__', 'b._.young22', 'lee_nature', 'classicgym_wonju', '_lipchori', 'y30m_j1', 'taebongg2', 'rongrong_tennis', '___syun', 'hyogy._', '173_58_', 'jjj_mini_', 'so_happy._.yeon', 'sajjang.mika.bae', 'richman.choi', 'kys422', 'healthy_hemzzi', '_.nobey_', 'long_jjoyyyy', 'mermaid_sera', 'zzul_tennis', 'yeounjin2664', 'ji.annn', 'eunsol_e', 'hip_pretty', 'shley_fit', '179_99cm', 'kwon218', 'for_semin', 'leehwoo._', '95.aayuna', 'la.delicatesse', 'kkokji7', '1.836m', 'daytokeepfit', '_n00b_2', 'pt_seook', 'good_minton_hanto', 'judy.3._', 'ssolsolala', 'dd_somi', 'ultra_minjung', 'pjw1013', 'rjx._.iron_97', 'taehoya_', 'o_un_finish', 'jackie._.workout', 'grace7777_413', 'healthdiary_jimmy', 'workout_mingwan', 'uh2kuya', 'sgym_maeng', '2sulman_', 'g.s.25_', 'suuu_uum_i_fit', 'sp.ssoond', 'hand_dianaaa', 'runlim_2e', 't.hyun_0830', 'whoslivvy', 'motion7_ansan', 'jinyyyy____', '8000o_o', 'o_w_0914', 'gaeng_63', 'jej._.minton', 'ddovely_blog', 'llliliiilllill', '158._.fit', 'hyeran7963', 'seo.gyo', 'sampyo_', 'purplekeem', 'seong_tae.96', 'weel_sh_coco', 'roniekyeol', 'korean_tank_nayeon', 'ganzi_ujin', 'dongdongk_fit', '173__jk', 'vulpes2353', 'heee.body', 'hoon0605', '167.5__', 'mu.ni7979', 'us_1024', '1.79v', 'ziselle2', 'king_make.up', 'fit__mdd', 'manzyy_pt', 'startover93', '_0.hoo.__', 'dietfood_na', '__morraaaa', 'linasclimbing', 'the_q_.0329', 'minjeongkang_', 'apricity_oung', 'hanhyein0307', 'hae_geunc', 'hellrin._.yun919', '_dndgml_', 'yans._.h', 'dynamic_n.n', 'fit_vibaby', 'nail_from_hl', 'ha.gisilda', '_an_km', '_s.y_jung', 'ray_homegym', 'zxx.9414', 'sse_187', 'seven_fivesix', '98_35fp', 'jenny_moonmoon', 'danny.works_out', 'inggoo_0', 'zun2_diet', '___jy.____', 't17581', 'jaeyoon_pp', 'steel_sson', '01t.__.y20', 'hyemzzi_run', '_gyuri_5', 'tigervintagedm_women', 'keem._.soda', 'snow_is3', 'sssu_nny_fit', '_168ba', 'luvmy_selfit', 'reset__ing', 'canbedoanything', 'mihee_showhost', 'mo.mo__tennis', 'ineninshop', 'bae_caa_', 'won_gyeong_lim', '176__sh', 'lyk79d', 'goodluckisalwaysmine', 'n_r.fit', 'lee.hu.ni', 'martin_1423', 'sasha_seulgi', 'santanda_eun', 'amali_1207', '_w.sournknoyut.___', '____baesisi', '2_ho__diary', 'sh10.25o', 'thisis_lydia_k', 'black_americano89', 'jay_workout__', 'mountain_e_ola', 'swi_im_hani', '_go_eun_2_3', '___suzy__q', 'xchaniee', 'thd_workout', 'k._.helen', '_bbizi_', 'jungriii_fit', 'ranee__fit', 'shin_yong_joon', 'little_so.nyeo', 'yh_the.heal', 'kim_jjong_ee_diary', 'take_it_2zi', '_9_h6_', '2chae_ni', 'fit_gymsu', 'everyday_with_me.s2', 'eungymmm', 's_lenaar', 'hys_ny', '0618._.seok', 'jin9_workout', 'hibss_m', '2_yoonji', 'lllli_1ll', 'kang_050701', 'nu_yey', 'cj._.an', 'ssooo_424', 'yunjisfit', '_j_0_u_187', 'lilly_______y', 'otht00', 'h_b_bang', 'gamsung_ljh', 'first._.cotton__', 'pilates__and', 'ttinker__bell', 'healthyeune', 'workoutjo.o', '__jerry.cho', 'workout_mingki', 'hel_gler_jjoo', 'j_wxn.1', 'jessiehoneypeach', 'daramjia', 'sonna_cycle', 'f__kingimmm', 'runner_kyu', 'itf_busan', 'fitness_ista_', 'hyoz_polez_', 'ukdonng', 'go9maxx', 'the_s_hape', 'dan2_kim', 'solbi_exercise', 'wkot_incastle', 'workout_day_', 'dear.beige', '007__728', '_fit_sm', 'k____jisung', 'hells._.o', 'soso_runn', 'parkjunsun', 'shine_s_bin', 'min.___.ju511', '0.jin_615', 'seoyul_workout', '__doit728', 'maso_y', 'ryami_fit', 'ddo_93__', 'xx_in_kwon', 'm2oweeeeee', 'iamriye_', 'bloom_fit_81', 'the0floor', 'jeen_star_', 'lovely_lovely1000', 'fitsoodal', 'zinga.173', 'jino_0419', 'lily_cocomong', 'c_r_y_s_t_a_l___l', 'goeun4767', 'na_sseun', 'thetis_fev_ellie', 'small___body', 'sinuna84', 'jeubini', '__nyjk__', '231days_', '167_s2_', '_chan_rilla', 'maxercise_rec', 'noeh__h', 'boseo_holic', 'hyejin.stagram', 'nurung14', 'jungyn_97', '5150_deundeun', 'zie_workout', 'ryu_seungcheol', 'doongtivity', 'haesiny', 'ghdfus86', 'xj_tennis', 'alumi_i', 'young.eeeun', 'santal_landa', 'hoooona_fit', 'kimnari_922', 'and._.0211', 'x_x_workout', 'yoyogoon_diary', '1995.sjh', 'l0venpeacee', 'imrosehan', 'q.e.d.sol', 'seoristar', 'god_shin_lee', 'shinhaley', 'k_yee_un', 'wellness_sh_s2', 'muscle_kh', 'kimkichul1202', 'ggan_ss_', 'je_21_0627', 'enjoy__move', 'youngju__diet', 'zumtree_', 'bbangddo2i', 'gyo____2', 'januaryoung_nail', '186.100.34', 'brandmall321', 'yllej_closet', 'yu_seong_e_', 'vine_pt_pilates', 'dlrudbs_wt', 'aeseon1126', 'taek2_91', 'lmrxxz', 'kkangdora2', '4u_pt_studio_2', 'yxxni_fit', 'hime__shuu', 'park02255', 'k____yllll', '1._.sumin', 'marie_0070', 'jisu_workout', 'yeonii_tt', 'nightynine_yo', 'bartender_jeanne', 'luhada_p', 'eundissi', '171_you', 'jieong__', 'hyena_hena', 'maybe__diet', 'clap__min', 'object.dali', 'j.h1_212', 'minjiiiiii_i', 'pila_xier', '0lin97', 'noheul.ing', 'a1__ceo', 'leejoobong', 'chnn__a0917', '_165.51__', 'soo._____.innnnn', 'juniyo_', 'ju___1029', 'sung_hyeonmin', 'yejin23__', 'eunbizrosy', 'peachy_workout', 'jahyun_ee_', 'justyoung__', 'ljw7799', 'jiwonii.__', '__zeenee', 'coach_rush.hong', 'jinee_gym', 'lan_vvely', 'dailymoon_0114', 'real__originalss', 'mia_pilates_hi', 'ka_young2000', 'yoon_summer_ing', 'exgichari13', 'diet_hyxxn', 'min_g109', 'jinilying_', 'rin._.0_1', 'eiioep', 'ive.celine', 'cmp_jieun', 'openchung', 'beglow.kr', 'bahnhana', 'solaaara', '1.1am__', 'loveae.p', 'goceu6', 'd_h.yeon', 'churi_shoot', 'minfit__', 'ye_yoon_', 'minzziroom', 'amo_bici_', 'daramzi29', 'hel_eung_ae', 'ss._.workout', 'sem_ingfit', '27_180.82', 'jini_0301', '1._.gabozago_', 'qooi_seonaseona_ywr', 'o_oceaneyes', 'v_street_workout', 'pp_arker', 'emma_allez', 'k_rystal_915', 'm._.il2ya', 'teidinus', 'mingso_exercise_diary', 'ifuofu', 'gayomii____', 'jjini_m_lover', 'ai.2000__', 'leemijeong_ee', 'jw._.92', 'limhanbeen', 'redmin_fit', 'eheekang', 'na._.nyoooung', 'zumba_phillip', 'hxxoxne', 'pink__ya', 'heal_rynne', 'jinnykim_pilates', 'eunji_ch_164', '_zzin_star_', 'major_gggggggyu_', 'pogi_hajima._.yulmoo', 'dbsrbeo', 'totaek24', 'flex____y', 'jangdani_', 'o___yeeun', 'nayom_', 'emily_ilsukwon', 'youngjoo_peach', '94yeonnning', 'ssoniiet', 'health.chobbo', 'sensible__ycyw', 'eun_ju_silver', 'iroulri', 'muscle_.queen._.yeon2', 'hell._.jjyuuu', 'haroro_ex_diary', 'h__lv.31', 'l_white928', 'yes_shawn_', '_ourmin', 'wildfox_lim', 'ofnrfo', 'rara_daily.fit', 'tkdgus0289', '_minutaurus_', 'd0l.vi_', 'oo__2_7', 'mustmove_official', 'ji_hye_d', 'hy0_seo', 'hsxxg__', 'jinfit_', 'claraluv2', 'emrrms__qoop', '_luv.hy0ni', 'chohappy16', 'woo.gi_k', 'nir__yoga', 'undong_heegoxx', 'ws_boxingclub_9', 'azure_jass', '159.pt__', 'xzztzz', 'psi_95_', 'iiin__youngg', 'dan100boy', 'ati__atti_', 'clara_run_blog', 'do_.ng', 'z._.eun_', 'eb__habit', 'ok_nanal', 'youth_gumi', 'bong_rani', 'junhmxx', 'rhrudha', 'shin.han', 'a_fiery_penguin', 'byuxxmxx', 'jiyoung_dietlog', '__myo', 'uribody_pro', 'o__pearl', 'joo__workout', 'a_timid_day', 'zzi_e.y', 'xodyd0411', '2doe0', 'nowfit_hyo', '95.08.27_', 'runaway_diettrain', 'hyo._.jj_1', 'choezuone', 'kind._.waterduck', 'c_beomi', 'dduugi_96', 'jm_12.08_ds', '935eunseo', 'hello_marin_', 'nawonison', '_suxny', '165.7_fit', '95_jh_', '9_2fitness', 'heiden_in_gym', 'undonghajoo', 'dalepapi_dale', 'ej01_15', 'hyeong__eee', 'ororanim', 'incheon_ladies', '_mimvely_', 'l._.taem', 'k.sm_157', 'victorygym_kr', 'm_fit.n', 'fithan_hani', 'juju_911', 'jinsunii_', 'stxxl_co', 'zimni.ttera', '2_sang.hyun', 'mink_mingvely', 'ddxhx.e_', 'onjeonhee', 's_e_2.fit', 'ohina_fit', 'min_5588', 'jjeong._.2eyo', '191__ys', 'healthday_uh', 'dssss__s2', 'im_your_.genie', 'dal.9_', 'sosohan___0', 'cf_3box', 'azykang', 'mumu._.2222', 'nimble_fs', 'hr.fittt', '__h.bee', 'y.eori', 'haor_riding', 'shn9481_fit', 'nnna__nnni', 'r.___mii', 'ekghdgml', 'iris.a__15.8', 'charming._.workout', 'yoomcy_', 'hieunbi_', 'allin_kk', 'ssumji_', '__hyeri2', '_ddoji', 'rawltn_00', 'dong_ho_fit', 'size.gym', 'rabi.daily', 'slow_bee__', 'tkpua_0318', 'yeppibbi', 'dear._.xhi', 'physique_junu', '055.ccd', 'luv_wooli', 'santa_yuns', 'jhzzang0512', 'ro_omyyy', 'j_____joy_', '_bunnybluebeach_', 'klminjung_', 'mitsu_ri2', '_ming_fit', 'hi_xeon', '_z_zzu', 'y___j_08', '2.____.s', 'leererim_', 'je.n__ny', 'give.me_this', 'diet_101.2', 'z_silver_workout', 'santa_seul', 'hye_____ji_____', 'ph_d_weight', 'yaeeuns_md', 'autumn_pila', 'gyunadan', 'yebin_5_', '2zzi.fit', '16_8.d', 'im._.heee', 'haewon.ching', 'erina966', '0_dahye', 'nakong__e', 'bing9rr_', 'jay.ss_1113', '_163.u', 'fitness__ssoo', '91_0315_', '__s0im_', 'jyjyj92', 'yeaaaaaah_d', 'h_aaaa__', 'gowithgym_sunttt_', 'shxxhxxeon', 'jelly.128_', 'yerin_pilates', 'ttonie._eat', 'jh.0814', 'h_b_dd', 'a.zure_ll', 'pilates_dy_', 'pila_byori', 'lhk._.v', '__daaaaa_2__', 'afpk_eunjeong', 'bootyful_bomvely1129', 'natural__su', 'oun__wan11', 'aurajudo', 'yang.heesam', 'jjja_hong', 'd______mmi', 'imsohotgirl_moi', '___9.05', 's0___0vely', 'da_unii', 'gonxyu', 'healthu_yeon_', 'practic_su', 'hell__zzi', 'newungze', 'work.0ut_b', '_sem_y', 'hpp_daily', '_9024_', 'zzze_nori', 'thisgroundyoung', 'svmyn_workout', 'h__s0124', '951219_', 'jeong_vida_', 'yuubi_fat', 'teminyeo', 'nauni.k', 'zuxeun', 'hyob_ang15', 'sshung22', 'iamzsilver', '_junilife', 'daon0136', 'pinkdawoon911', 'kyuya_life', 'ddumi47', 'xxptto_x', 'sundae_abba', 'a.bit.mor', 'seongjoong.e', 'ziiiiindiet', 'do_browne', 'happydidu', 'aqua_s_jm', 'dew_0603', 'needs_kr', 'm1nvelyy', 'daae.et', 'zzewoo_fit', 'jwoo_c', 'greek_yogurt_master', 'aus_ome98', 'isoyun1843', 'gre_hiking', 'tennis__kke', 'healin__ming', 'tennis_dyong', 'groovycandy', 'a.mi.young', 'minsssunny_', 'ssonny.like_', 'green.shop.co', 'sso_phi__', 'ssg_instaa', 'ju.yoniyoni', '0nce_fit', 'm._.m_fitness', 'yebini_exercise', 'pilates_yubin', 'rool_roow', 'h_soriiii_', 'do_ro_dong_dong', 'bakyo_o.fit', 'diet_diary__o.o', 'xx__se1219', 'line_lym_dana', 'ej.ing', 'wxndx_k', '168._.babe', 'resyve_', 'hellin_jjoo', 'wellfit_jiyu', 'halucky_ns', 'health_shugi', 'mustfit_r_i_n_00', 'chunza_no.5', 'dahye7523', 's_sports_lover', 'jju_dailygram', 'san_y0ung', 'fit_me_mi', 'ssun.mimi', 'circle0_0wony', 'melove_93', 'konni_i_am', 'yella_b38', 'b_ari310', 'wxxn_h', 'ggangsso_', 'lo__un', 'pila_gh', 'ruddlgram', 'yogini_hyuna', 'studioakion', 'pila_suyeon', 'mi_body_', 'jeong_yoga', 'sunaeyoga', 'ssu_a_seo', 'yogini_hyogini', 'my.free.time', 'thvyoer', '160.8_jl__jl', 'regina0235', 'j_o_ob', '__ssjjss__', 'lenaaaaa.k', 'sarang2_golf', '0108_2_96', 'pepper.rainbowls', 'dawn.haneul', 'fitjungah', 'yuil___mui', 'seoyoung_170', 'a_y2e', 'zamilakilla', 'j00mi_', 'heartracing_1', 'csjzzang9246', 'ssaemith', 'i_da_silver', 'imbeauty8888', 'pila_luv', 'yoga.fitness.in', 'beliefgym_kbh', 'suyaaa__aaa', 'hnu_n9ram', 'mel.on.a.diet', 'yu_lim_95', 'hanafit007', 'parkyasu300', 'another_people0727', 'jk_rhythm.tr', 'ryunie86', 'jjuming__820', 'ming__workout', 'joo__082392_', 'ye_explorer', 'jiny._.s', 'kimj899789', 's_h_kyo', 'sso0_diet', 'ddoni__ddoni', 'life_do.o', 'golf._.jiny', 'arijung_729', 'ho057_pila', 'rrrrrosedu_', 'alex.ahn', 'golf_mingming', 'seungil._.choi', 'y.chaehyeon', 'pushminda', 'son_stargram', 'mj_07.18', 'ssuna_s', 'ribbongirl_golflove', 'cherry11jju', 'jju_0530_', 'm.m_x.x.x.x', 'cjswomini', 'minpilates___', 'vorah_de', 'onlynail_on', 'pilates365yh', 'dxng_xu', 'nailhave_', 'fit.macho', 'sun_gee_', 'min_a923', 'bonitapilates51', 'ppgym4', 'dhdltmf_', 'artist_jiwoo', 'jibang_bbeja', 'ody_____e', '_naomi.mariposa', 'ssun_miiii', 'o_un_wan_23', 'wonzsnv', 'highend__ys', 'seon_h0_', '0002.19', 'chocho_won', 'g.hui_s', 'kjutation', 'captainpilates_dan2', 'rhythm_snow_', 'good_enough_book', 'yul._.98', 'clpilates_ulsan', 'mount_hyeonee', 'won_09.08', 'jongsu_430', 'mrs_castle_', 'h.__.star', 'label_lee_', 'jennyis_awesome2', 'leeyejin_7426', 'gymdoyun', 'imirabel_official', 'm_aina_01', 'ddaz5s2', 'iiiroun', 'pilates_ma', 'minvely_workout', 'high_fit31', 'skye_yoons', 'bodyus_seok', '_bin_stargram', 'queen_anna20', 'zumba__lany', 'ga_eul_pt', 'yun_huively', 'yeon_su_love', 'phantomgym_official', 'tg_swoo', 'allpeople_p.j.h', 'daehxxn__', 'hotplacegym11', 'tp_dhk_92', '2mippeum', 'trainer_arnolgu_', 'fit_h_y_94', 'jojun__0', 's2__u__', 'i.m_sem', 'best_kyung_', 'neiel_official', '158.ex_diary', 'yebin198', '_ya._.s2_', 'jumping_seosan', '16o_57', 'narea_vv', 'oreun_n', 'jjung_hee98', 'burpee_syndrome', 'dae_01_15', 'my_suya', 'myungzzoo_lee', 'cherishedjini.ver2', 'douce.hyun_', 'summer_nhj', 'damsongyorihada', 'tonystark0221', '_ha_hyeon_', 'whisen112', 'beast_best_park', 'jung__dw', 'hotplacegym10', 'skdlslw', '__03.12.01', 'w_dong_', 'asfit_gayoung', 'hjcsportskorea', 'eun_ji_daaa', 'xoxogunxo', 'ichbin_rach', 'physical_job', 'serif_j', 'ef.pilates_', 'guy_ms_', 'seul_in_record', 'wonhee_hong', 'yoga__hanna', 'by_glam1', 'go_mollygo', 'joy__.jpg', 'santa___jvely__', 'jiu_fitter', 'jiny_jico', 'lsangeuni', 'o.ne_fit', 'power_pd', 'an_na__u', 'cye_jin', 'hyesoo_1', 'cookuza', 'yamchae__', 'boxing_moo', 'hawa2ii', 'kkm_hq_gangnam', 'note_oder', 'mr.cha_ys', 'snu_judo', 'riwon___9204', '18.jsy_05', 'hena_hyein', 'violet.jung', 'ha_vely____', 'victoria_fitstory', 'hhhyunn_11', 'yoon.d_', 'victoria_ej61', 'on__simm', 'yeoshin_0415', 'ys__lee04', 'seung.il_', 'saoiilz', '1004gony', 'luminous__ys', 'eun_yy_02', 'sssujee', 'elu_baby', 'hey.o_o', 'favor_pure', 's_moon11_', '_yeo_ning_', '01__l2', 'holasu_', 'vivi_8685', 'jinxxbro', 'ohminho_1027', '______hm.k', 'roiju_kr', 'zal.fitlife', 'yoonha__official', '_yeon__jj', 'jaey__eon', 'y_na_2020', '98.03_27', 'ha._.binii', 'ssim_eunue', 'kkkjmkkk', 'leeeeminkyoung', 'workout_hyerim', 'mj0712_kim', 'yeo4_king', 'luiilu2_', 'woori_k_91', 's.mirae', '__delay_k_', 'hong_.11', 'zzap_tang', 'dk_ide', '3years_96', 'dear_dain0109', 'nina.chong', '7star.dia', 'pharmacistella', '9mi.0ju', 'eunstar1101', 'u_jiaterdot', 'm.j_kim74', 'b.h_u17', 'araariyo', 'sss.enter', 'cmy_ceo', 'skh2_2', 'bella_carmi', 'onethingaday_', 'lihavell_pole', 's._yeoniiiii', 'youn_pilates', 'jewdri', 'muscle._.moo', 'mimi.ing', 'yoonayang', 'la__bee_ni_', 'wrestler__k', 'sooyeon21004', 'della_linda_7', 'from_holy', 'munseok185.0', 'damheeee_', 'bluelemon204', '85parkjang', 'trehny', 'gim.6744', '0812_ssj', 'poohdory1', 'over.ring', 'ggu_1112', 'instyle_hee', 'hyennie_._', 'bbybyoun', '2.4_ljm', '170__jo', 'wc__js', 'raniet_94', 'april_jang_julie', 'mmmming_a', 'xh__jungx', 'songfit__sy', 'hi_zzeng2', 'honey__ddanzi', 'm2n_so', 'yubin__kang', 'hyunbeeny', '45__fit', 'tennis_ardor', 'what_a_shot_gi_joon', 'lullului', 'yu_jin._.tennis', 'ej.tennis', 'peace_kxx', 'draw.ham', 'u_ringding', 'tenn_is_o.o', 'tennisclaraa', 'zzzini28', 'proteinu', '_ming_min', '_ming_o0o', 'soya___pro', 'jw_lppeu', 'hairgung_ja', 'jaycho89', '88._______.88', 'shee_cheol', 'simeunae_zumba', 'jeonhyojeong5', 'may_9_melody', 'choc.o____', 'dbsdk0703', 'pitch.and.run', 'h_dare_u', 'azure_park_01', 'dear.seol_', 'elinbii__', 'limyoujiny', 'jooooo___w', 'han.sooah', 'minji2ppu', 'bslabel__official', 'gaheon___', 'yeowoo_b', 'young_ss8660', 'nabi.nalssini', 'its_neulbo_time', 'siaka3_3', 'limsseyo', 'hyeong__________', 'withbee_official', 'e.jayleen_', 'jjin2stagram', 'coucou.fit', 'euneun_uu_', 'oookkk33', 'bae_r_r_r', 'yooa.y', 'llllose_sy', 'euijooss', 'seu_oen', 'a.peachu_', '___.zia', 'allie_0227', 'mown_tour', 'haho_haaahooo_o', 'k.ju__h', 'hye_leeme', 'sk___seo', 'muscle_sudong', '___ze.ze', 'its_gym_soyoon', 'ridingaga', 'su_jung87', 'jisoo.x.x', 'jeje.newproject', 'm_n_u__3', 'bodyfit_yul', 'yang_songhee_', 'kang_16.04.12', 'lovely_jjinju', 'best_choi_', 'mi.log_', 'yoon2o', 'answer_fitness', 'eunnnnn0814', 'eunbox', 'julie9065', 'eunii_.157', 'youm1030', '2sunbro', 'red_daisy__', '2heeyagram', 'happysijoo', 'dam__diary__', 'strongzero_kr', 'metree_mall', 'pol.glory_01', 'ji__o619', 'cherry__hong__', 'jiyoung.lee100', 'miyongsik', '_yena_kim', 'mnfitness_official', 'love0825ff', 'juubbly', 'suk__jae', 'woojeong_z', 'ydg__0304', 'yanggeunhee', 'firstbody_gym_pilates', 'bae._.derella', 'feel_geun', 'ssunny_7777', 'dani.__.dani_', 'one_dietday', 'ssoramz', 'llynnnn__', 'roni_table', 'ohkyusun', 'p____byul', 'sooinkiki', 'jina_pilates', 'super_mins9', 'yuldong_s', 'health_rim', 'i_inxxi', 'hongstar2016', 'hssm011', 'habini_aa', 'mo_on.zero', 'namjun_kkk', '185_j', 'urban_jiujitsu', 'da_younggg', 'hipple_ze', '_k__sb__._', 'hye_ppeum_', 'n.aelii', 'yoon_move_', 'taeho_ham_', 'jiah_0527', 'srmozziroll', 'alphapurple', 'h__booty__s', 'yeunjji', 'psh__9', 'fit___hyeon', 'moonjh_ch', '2ogram', 'dietstine', 'ssssujin__', 'jun.2275', 'moonhyuk_jang', 'jeonhyemi0621_ifbbpro', 'dayy.gram', 'mongsta88', '__a_yeon', 'healthy._.chuthy', 'whitescus__', '0nly___won', 'woo._.vely', 'heiilin._.up', 'jeju_yun_yang', 'luv.joi_', 'kkk.yj___', 'h._.raning', 'jemissong', 'mialove1004', 'dlffjtm', '_ckjin', 'a_ssonghee', 'llool0looll', '5yeonsu', 'ssangb4840', '_mangnani_', '_ej_kang_', 'hexercise_14', 'zzzung__2', 'kunny_k', 'name_daily', 'maison.de._.eunjoy', 'zero_ssunny', 'kayoung_koo', 'h__nm_n', 'yw.tr', 'kwakjieun2422', 'sunny.gibbab', 'hulijia0206', 'merci.you', 'hyeogihyeon', 'attractive_031', '0315__js', 'juuu_0104', 'rachel_ty0', 'hana01071228', '__yh424', 'roooooocs', 'pinnnymph', 'sun99_moon99', 'mijin_aa_', 'parisjung', 'moogstar__', 'builder__lee', 'modernroom_yuyu', 'yuhyel_', 'joyful_127', 'image__90', 'hoon_1814', 'g________day', 'rubang_myeonjak_inhye', 'sunghee_44', 'seojuyoung1128', 'queenmun', 'jcm931213', 'castle_sm', 'jjeongsmom', 'sensitivity_hyun', 'hy_golflove', 'ria93lee', 'jae_hee__91', 'kang_body_', 'yoonyul_07', 'weonyun_27', 'you_easy', 'jinikwon_jeju', 'vdongmin', 'lulu__gayoung', 'hyen___k_', 'kyoungmi_choi', 'yoojeong0128', 'flutterer_camper', 'xognsl0120', 'kobongcat', 'seogangs', 'han_yujin_78', 'ssandy1983', 'hong.ssseung', 'master_trainer_b.a', 'lucy._.1229', 'leekoeun2016', 'soobean_o', 'sm_tiger', 'hwizin', 'shinaebabee', 'semvely__fit', 'jungbona', 'hj.k_pole', 'scelidopilates_jongam', 'joonsun_fit', 'heojae_', 's.___wc', 'jason_fit5gym', 'justdoitvanessa', 'j._.young_e', 'hyuni_fit', 'hyogym7_rosa', 'hyelthy_dh', 'hongra3075', 'olivia___choi', 'healthyyon925', 'healthy_jji_land', 'h_yojinee', 'minii___ly', 'luvin_victoria', 'dahwi_eli', 'e.j_choi', 'colorpole.d', 'k__ot.natural', 'cho.zz104', 'diet_kdy', 'jjoo_1115', 'cacheru11', 'bodycaregym_', 'jheal_official', 'jangddaeng._.e', 'bella_cherry06', 'j.eun_pole', 'cha._.y_lim', 'its_gym_hyeon']

    ##2. 유저 분할
    total_user_infos_group = divide_user_infos_list(user_infos_list, group_size=1)

    ##3. db 발송
    send_total_message(total_user_infos_group, text, project_name=project)
