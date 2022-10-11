import json
import math
import sys
import requests
import time
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
host, port, proxy_username, proxy_password = "resi3.ipb.cloud", "9000", "AX7S3xZk5L9RF1So", "wifi;us;;;;"
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

def select_user(username=None, client_name=None, max_messages_per_day=None):
    account_setting_info = INSTA_ACCOUNT_OBJ.select_and_update_user(username=username, client_name=None)
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
    response = client.user_info_v1(user_id=userid)

    return int(response.pk)

def get_user_id_by_db(username):
    doc = USER_CHECKPOINT.find_one({"username": username})
    return doc["userid"]

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
    project = "dan"
    ##파일이름
    filename = "dan"
    project_start_date = "2022-10-11"

    ##제외할 단어 유저이름, 프로젝트 설정
    exclude_word = "official"
    exclude_word = None
    # exclude_word =
    exclude_end_date = "2022-08-05"
    exclude_start_date = "2022-08-05"
    exclude_userid_list = completed_target_influencer.find_completed_influencer(project_name=project, start_date=exclude_start_date, end_date=exclude_end_date)

    exclude_userid_list_int = list(map(lambda x: int(x), exclude_userid_list))
    exclude_userid_list = exclude_userid_list + exclude_userid_list_int
    # exclude_userid_list = []
    # exclude_username_list = ['iayoung077', 'hyun_ha_zzoo', 'm_minju_', 'lee_beautysalon', 'choi_r_im', 'min.sooa', 'sukyung__k', 'h._.raning', 'im_ssong1201', 'lovely._.gamoong', 'drmyskin', 'barbieunni', 'ss__ming_', 'mino_riza_', 'm.e.pilaa', 'je_j8816', 'lovely.___.su', 'hyongjookwon', 'mootn.go', 'remain_rin', 'moi_bom', 'daily.hyeon__', 'rosa_mylovelydays', 'nanicho__nancho', '116zzzzz', 'soojung0407', 'wootgosalza', '_bambaya_', 'jaehyuk_wkp/', 'hyunjudal', 'chae_min_0824', 'seullv___', 'eun__kkk', '__joo79', 'ej.day', 'hi._.tamna/', 'ddooo_sports', 'hyunihyun87', 'Jinny_0811', 'sienna___j', 'aliceisalluring', '1_aang', 'wjddk_s', '0rorimarket0', 'ppickssary', 'hyongjookwon', 'do_na_vely', 'julialuvyoi', 'miss___bling_bling', 'hyelaan', 'lgl_master_han', 'jessica__dailylife', 'bebebo8787', 'shslike40', 'iameve1222', 'mycrystal007', 'remember._.bt', 'adela__j', 'js___leeee', 'bnr.kim', 'songloves22', 'ka_hwi', 'coy.min', 'yulyuri.k', 'jiii_home', 'strawberry_min809', 'nxyxxo2', 'happy_panda_story', 'doyoumommy', 'heeju_style', 'da0123da', 'amateurgolfer_luckyguy', 'siyu_an_', 'bo_ora_golf', 'shannon_ryu', 'charlezfit', 'js___leeee/', 'muse_golfpilates', 'moon.fit_', 'airfamjjin', 'dreampharm.jennymin', 'enoughgarden', 'js5288', '___e.you', 'aimee.hello', 'thanks_two5', 'ji_hyun_diet', 'noonaistory', 'havelycloset', 'duttalmom', '___byann', 'here.j', '1am.rane', 'mom_house', 'saeron_queen', 'luvjemma', 'j_and_view', 'nana_showroom_', '181213_hy', 'f.our.l', '_itsawesome', 'e_ddoll', 'namystar__', 'jjenny_jeong', 'victoriahoom', 'kelley_mk_kim', 'jazzzzzeee', 'uyyunx', 'relovebyis', 'beta_mom0208', 'louvre1004', '_jinuary_', 'Kkamang__cherry', '_vely_j__', 'jjoom20', 'me.suebin', 'pinkrabbit012', 'suji_gram', '52_ne', 'kimyonggwan5003', '_woobin0831', 'Joovelyyy', 'helloranyy', 'sweet_label_', 'blancmoon0', 'haileyy___k', 'ljueun._', '053_life', 'k_raheee', 'jennet_pilates', 'ggomagom85', '2___zzzu', 'danlyun', 'ok_unni.2014']
    exclude_username_list = []
    ##타겟 해시태그 설정 해시태그 설정하지 않으면 프로젝트 이름이 default 로 들어감.
    # search_hashtag = "물광피부 효소 모델 나들이 카페 가을 뷰티"
    text = get_dm_source.get_source_message(f"{project}.txt")

    ##몇개 가져올지
    skip, limit = 0, 1000

    ##서치 필터플
    # user_followed_by_gte = 7000
    # user_followed_by_lte = 900000000
    avg_like_gte = 0

    user_infos_list = ['juliastoryroom', 'miniming.90', 'deng.cook', 'kihyun__23', 'riya_yoo', 'aileen.ejk', 'chase.hjs', 'onjjun', 'party_lespetits', 'seowon_mom0922', 'lazy_mom_o', 'namji_b', 'binini_5', 'bbo__bebe', 'lovely__rindo', 'thinkeco_official', 'hyoju9487', 'mimignon_', 'dadavely_1004', 'miuhanbok', 'i.yuseul', 'at.her_', 'cherishbebe', 'kivaparty', 'smile.home_', 'hansookjun', 'bonnie.myel', 'hohomoms', 'bomnal_s2', 'eunhye714', 'koongkoong2_', 'turningpointgym_ceo', 'imhaeji', 'pastel_bubble_official', 'ji_young0608', 'lovely_sh0250', 'moyou2u', 'duranduran1119', 'ysongvv', 'm_h91_24', 'kko_mance', 'misssim._', 'dalbit_table_official', '__ji._.hee', 'jo_eji', 'dk_jj', 'elsir_premium_living', 'yullvely', 'bo_ssami', 'jins__jk', '_ohyohan', 'dadamama__', 'vienna.foot', 'rangfilm_', 'osena1381', '100mihwi', 'aroshop486', '____i_na_', '_joymama', 'gonogono_story', 'olympic_ttuckjip', 'balloon_de_j', 'heejin.kang', '__im_ceo', '___hyo_0714', 'pinksmell2', 'o__oxox', 'myspecialhealer', '89s90s16s', 'jiyul___vely', 'baegotdaek', 'hwan__ma', 'influencer_tei', 'keenz_lebere', 'kkonnnjeong', 'hosun_', 'jeh777love', 'plafarm', 'coach_koo', '_byeorrri', 'mj_pooya', 'jane__aus', 'feelsogood_h', 'sisoballoon', 'cooking_ohha', 'hi_lottomom', 'haha__y', 'k_ahran_m', 'yeong_graceyaksa', 'kamin_closet', 'masta502_', 'by_jenny83', 'rona._.mom_', 'kiki.yaong', 'atti__j', 'dear.jye', 'yooja_family', 'six.zzal', 'luv_mom_0429', 'hello.little.sol', 'orange.zzal', 'to_naeunbaby', 'happydana_', 'kkalkkal.enter', 'three.zzal', 'ggomoosin', 'mimi1121_', 'loveyoolucy', '48000_flower', 'i.dol_love', '_king_enter', 'goseokbin_', 'artistic.thu', 'norang.zzal', '_chu_eu', 's2_umnal', 'enter_lulu', 'songckzzang', 'kikipoint_55', 'kkuhankku', 'kkokko_tiger', 'ain__mm', 'bibim121', 'insight_celeb', 'nicklee_.dk', 'vertblanc.official', '9194_eun', 'ogoo._.59', '__jjinvely', 'bebefitplus', 'limongbebe', 'ji.sunny__', 'dda_ami', 'sissysally2', 'byulingya', 'beige._.n', 'suumung', 'hana.bong', 'woong.daon', 'sujin_sue', 'duri.official', 'yeoni.e', 'im.juyoung', 'jiwoo__0802', 'luv___mini', 'chanjongi_life', 'misotable123', 'seony_lim', 'eerae_', 'jinky2011', 'itsme_hjy', 'sils_handmade', 'suna._.nk', 'roencoco_official', 'betvogi_kor', 'onjeonhanharu', '5a_rin', 'khjangell', '16.1.31', 'isunyeong901', 'seogaonuri', '__arles', 'iyumom', 'totory1503', 'my_daeon.ria', '__kimsaebom', 'woo______a', 'vilang_official', 'yul_mam727', 'vividyooni_', 'ggosirang_table', 's0n9_b0k', 'creamsafari.official', 'homemadefood_recipes', '2bin_mom', '9wol_enfj', 'mint_dress', 'bodyprogramer', 'powamung0921', 'liseo__._.__', 'jin_11xx', 'up_sunsun', 'baebae_0205', '85.amy', 'luv__ayooni', 'bbbbichaa', 'yallelee', 'sonsoogarden', 'have3_11', 'taekyeong_food', '0807jiyu', 'orzin_n', 'yeoshin_0415', 'hwanggirl_', 'happy.euntto', 'yoontree15', 'k_commu_archive', 'bbamma287', 'misslovelycloset', '2daaam__2', 'kimis_market', 'judy_happylife', 'ssongi__h', 'gil.life84', 'bebeyule', 'waniyun_', 'makingn__', 'blooming_jjsy31', 'daldal_vv', 'baby_roh_', 'narae_grim', 'dalkom.sweet', 'ujoo_uha_luv', 'yeyul_luv', 'hong_carol', 'danbiko_', 'starbebe__', 'jeong._.jihun', 'jenie_sss', 'haedeenee', 'sarahktravel', 'da_eun_mami', 'design2dainn', 'd3_twoseul_mom', 'rara_____n.n', 'gina__jeong', 'yeonwoo_ya', 'ddbb1004', 'piopiomommy', 'ggomsmom', 'angolo_milano', 'woo.a_mom', 'soooon_0.0', 'cake_space_', 'sandiblossom', 'ji_angtteu', 'happyhobin', 'jian._.mom_', '_love.jooo', 'ha___na_o', 'bebibebi_', 'ladydessert_', 'toooooori_', 'kmj1004m', 'kil_84', 'fraisbellon.official', 'our.eunyul', '_xxkwak_', 'cledor.montessori', '__tae_ri', 'yuju_vely_', '_hamnammae', 'mosmos719', 'sarang._.2022', 'log_sunwoo', 'mmmina007', 'k._.sun', 'rayul_mom_1117', 'soogguri_94', '1025___bubu', 'arin__vely_', 'cclim.j', 'jammuk.project', '_royday_', 'deepnap_19', 'kkul.doyul', 'm.hajuuun', 'bellahjkang', 'kwon._.yul', 'gyeom.3', 'jane__ttt', 'double_dragon2', 'hy_moms', 'silverdragone', 'play_read_grow', '00mi0mi', 'baby_josieun', 'hye.wonder', 'bebe_soyoon', 'hi.wooye_', 'hr_yisol', 'snsao', 'bbbo_ye', '_jiiiiii_baby_', 'onziya_', 'rachelmj_shin', 'aumom811920', 'kkomzi_closet', 'euns5', 'kirikiri_mk', 'rod_a26', 'calilifeoc', 'destinyjin37', 'su_.min1004', 'bossmaeng', 'yd._.yoon', 'papadal_insta', 'su_kky', 'nooneelselikeme_', 'sarah1004k', 'layday_y', 'wannabeys_jm', 'etre_sso9', 'dam1_1oo4', '_danb_b', 'kkong.0110', 'mini921121', 'aokiay', 'hoo__1116', 'bebe_108_206', 'ejae_echan', 'little.inno', 'alicia_jihyun', 'hello_beenbeen', 'eumyoungeun', 'nanana113', 'rachel_ky_cho', '2dam2jun2som', 'seraphic_arami_', 'raonbebebe', 'in_ah.love', 'ww_design', 'yangsoois', 'lovely_s02', 'my____hana', 'tae.___.vely', 'eugenefarm', 'hahahoho12180', 'woorin__house', '___s___e___o', 'lime_bella', 'soi____mam', 'ggostar_baby', 'h_yujoo_______', 'lovely_____suzy', 'bumimummy', 'siaa1004', 'j_yun.u', 'duswn9005', 'mc_chars', 'yun_jae.c', '_jjjneoy_', 'today_bambi', 'jco._.jco', 'sihoo210821', 'sso_jung26', 'like._.yoon', 'si__ne.chuu', 'jjokkomom', 'cotyledon2021', 'janey_paterson', 'haeon_haesol_luv', 'yedam_hkc', 'wowowow_0520', '_woobin0831', '_jayi_jayi_', 'yuhyun_si', 'lululala707', 'jangyuna_chanel', 'universe_c_', 'by_mijoo', 'jung._ej', 'smscucu_10', '__yul_mom', 'night_sky1115', 'oro_ily', 'luv._.jaeha', 'carol_bykorea', 'dmkcurtain', 'jjun___u', 'about_ojh', 'dahyelee.32', 'thewoomije', 'from_bobo', 'tnickle_bookclub', 'kwak_danb', 'h.inhosoyoon', 'hanakang0503', 'luv9min', 'nkm3378', 'welcome_blessing', '_isolbebe', 'hhhhh.a__', 'sunrise_mmmin', 'janenstory', 'banila27', '925h5', 'wanimom_2021', 'statice_', 'ssu_luda', 'sonjjirung', '_je._.rry_', 'dohane__', 'ssm.5105', 'lulululu_woobrother', 'bae_so_yul', '_jenny._.vely_', 'maehwa9148', '1stdreamers', 'especially00', 'jinsune1', 'jjjiyoniii', 'dabro_story', 'davidk.7', '86.j', 'jessica_201511', 'reo_0825', 'hih_i333', 'hi._.yunbebe', 'mozzi__o.o', 'yoonsdaily_', 'the.bridge_iany', 'bombom0322', 'i__luv__yul', 'ddongji_m.m', 'yeon_yeseo.lee', 'for__uuu', 'woojin113012', 'yoona_papa_0822', 'ginny_bb', 'picturebook_curation_for_u', 'bkpuroon', 'chlsuzeng', 'wngml715', 'nobel1220', 'baby_hero.tg', 'zzumez_couple', 'soojin5949', '__rin.woo', 'havely_0102', 'joo._.mom', 'doyul__mom', 'doctor__saran', 'ra._.mmi__', 'one2log_', 'imlash_sun_', 'j123_mom', 'to.jungeun', 'heo.sudal', 'ddudi.jjongs', 'nahee__20160216', 'dasomi___iiiii', 'lhj4742017', 'seohyeon__papa', '___hermoso_', 'by_ssun2', 'ha_yul_pop', 'chan_daddy_gram', 'sangyeongcha', '2w.mom', 'k_hee_eun', 'seha521', 'bebedog1', 'icrayon_miae', 'yoona11066', 'icyrain798', 'lii100331iil', 'alalxx0822', 'bbaeck_ia_b', 'woo.love__', 'raddo_bebe', 'b9toon', 'tamimamang', 'soso_ppp_p', 'hyun2ne1', 'himom__2', 'sky_22222', 'leegajin', 'latte_yul', 'otter88yun', 'eunseol_mom', 'rumi.jj', 'teddymom_ahsol', 'its_kareni', 'jun._.baby', 'siaseoamom__em', 'sook_420', 'okipark', 'modseunji_', 'ppu_daily', 'babelkimm', 'kyung_a_choi', 'jwonny._.b.c.mom', 'd0nghye0n_lim', 'sukkyungmill', 'kkoma.ato']

    ##2. 유저 분할
    total_user_infos_group = divide_user_infos_list(user_infos_list, group_size=1)

    ##3. db 발송
    send_total_message(total_user_infos_group, text, project_name=project)
