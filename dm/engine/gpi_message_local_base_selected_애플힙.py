# -*- coding: utf-8 -*-

import json
import math
import sys
import requests
import time
from dm import config
from dm.engine.gpi_auth import login_v_gpi, login_by_sessionid_v_gpi, select_user
from dm.engine.user import user_split, divide_user_infos_list, push_influencer_completed
from instagrapi import Client
from instagrapi.types import User
import logging
from instagrapi.types import DirectMessage
from instagrapi.exceptions import UserNotFound, ClientForbiddenError, ClientError
from db import m_instagram
from db.model import *
from dm.engine.exceptions import *

from dm.prepare import get_dm_source, get_influencer
from dm.engine.gpi import get_user_id_by_username_rapid_api, get_user_by_id_lamadava, get_user_by_id_gpi, \
    get_user_id_by_db, get_user_by_username_lamadava

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

max_login_try_num = 2
max_messages_per_day = 200
max_group_size = 30


def infinite_login(client: Client, username, max_messages_per_day, client_name=None, session_id=None, proxy=None):

    while True:
        ##1. 사용할 계정 DB 에서 가져오기
        account_setting_info = select_user(username=None, client_name=client_name, max_messages_per_day=max_messages_per_day)

        if account_setting_info is None:
            logger.error("사용가능한 계정이 없습니다 infinite login 을 종료합니다.")
            raise AccountException

        ##2. 가져온 계정으로 로그인 시도. session 받아오기
        # try:
        #     session_id = account_setting_info["session"]["sessionid"]
        # except:
        #     session_id = None
        if session_id:

            login_session = login_by_sessionid_v_gpi(client, session_id)
        else:

            login_session = login_v_gpi(client, account_setting_info["username"], account_setting_info["password"])


        ##2.1 가져온 계정으로 로그인이 성공한 경우 받아온 session을 return 해준다
        if login_session:
            # client.pre_login_flow()
            account_setting_info.update(graph_session=client.sessionid)
            return account_setting_info

        ##2.2 가져온 계정으로 로그인이 실패한 경우 계정을 새로 가져온다.
        else:
            continue


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

            valid_user_id = get_user_by_username_lamadava(username)

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


def send_message(client, user_infos, text, next_account_info=None, project_name=None, proxy=None):
    max_account_retry_num = config.max_account_retry_num
    max_request_retry_num = config.max_request_retry_num
    request_retry_num = 0
    account_retry_num = 0

    ###next_account_info 가 없으면 계정을 가져오기 있으면 해당 계정을 사용한다.
    logger.info(f"next_account_info:{next_account_info}")

    if not next_account_info:
        account_info = infinite_login(client, username=None, max_messages_per_day=max_messages_per_day, client_name=None,
                                      session_id=None, proxy=proxy)
    else:
        account_info = next_account_info

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

                # client = Client()
                # client.set_proxy(dsn=proxy)
                account_info = infinite_login(client, username=None, max_messages_per_day=max_messages_per_day, session_id=None)
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

                if e.__class__.__name__ == "ChallengeRequired":
                    INSTA_ACCOUNT_OBJ.account_collection.update_one({"username": account_info["username"]},
                                                                    {"$set": {"status": "unavailable"}})

                if account_retry_num >= max_account_retry_num:
                    raise AccountRetryExcessException

                # client = Client()
                # client.set_proxy(dsn=proxy)
                account_info = infinite_login(client, username=None, max_messages_per_day=max_messages_per_day, session_id=None)
                continue

            logger.error(f"client error:{response}, retry request // request_retry_num :{request_retry_num}")
            continue

        ###dm 발송 성공

        logger.info(
            f"디엠 발송 성공 username:{username} /password:{password}/ sessionid:{sessionid} -> user_info:{user_infos}")

        ###dm 발송량 +
        INSTA_ACCOUNT_OBJ.account_collection.update_one({"username": account_info["username"]},
                                                        {"$inc": {"usage.dm": 1}})
        account_info["usage"]["dm"] += len(user_ids)

        if account_info["usage"]["dm"] < max_messages_per_day:
            next_account_info = account_info
        else:
            INSTA_ACCOUNT_OBJ.account_collection.update_one({"username": account_info["username"]},
                                                            {"$set": {"status": "available"}})
            next_account_info = None

        ###
        push_influencer_completed(project_name=project_name, start_date=project_start_date,
                                                              influencer_completed=user_ids)
        return next_account_info

def send_total_message(total_user_infos_group, text, project_name=None, proxy=None):
    next_account_info = None

    client = Client()
    client.set_proxy(dsn=proxy)

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

            next_account_info = send_message(client, user_infos=target_user_infos, text=text,
                                             next_account_info=next_account_info, project_name=project_name, proxy=proxy)
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





if __name__ == "__main__":
    ##project 이름 과 제외할 프로젝트 이름
    project = "able"

    ##파일이름
    filename = "able"
    project_start_date = "2022-11-05"

    text = get_dm_source.get_source_message(f"{project}.txt")
    user_infos_list = user_split("""""")
    print(user_infos_list)

    user_infos_list = ['chong._.da', 'sy_shin__', 'chj8442', 'bokbunjajoo_im', 'l____._.____sh', 'banastin0401', 'luv_hh_luv', 'x_of_closet', 'ssola_official_', 'biny_j', 'bike_love_korea', 'spbmgzbmw831772', 'betterthanlife_official', 'beneider__joa', 'uni_109', 'sook_0', 'athleteinsta', 'ar.basket', 'soo_mus', 'angcherry_', '_mlmond', 'kyeong_54', 'trulyee_', 'sinzi.zip', '_luna._.j', '_dear_hyo', 'se0_hui', '03.14.la', 'rarara2.22', 'ramsbalcony', 'pilates_sol_', 'a_m_d.v', 'xinimay', 'jnkj_j510', 'pilajung._.eee', 'pansy_purple_', 'honeydam__', 'mookgozaza', 'nya0_8y', 'yoga_jini', 'yeon__d', 'oxil_zi', 'neon.swan', 'y___j_', 'syungah_peach1109', 'nailey_pila', 'sunnyhanofficial', 'sub__meoy', 'ji.u.0113', 'octopus__h', 'miyeon_070320', 'su___j_i', 'st.hoonx', 'mimi_loun_', 'som.candy', 'soh.ealthy', 'minbeeee', 'lovely_bome_', 'shinvelys2', 'se.a_jin', 'kimyoojungphilippines', 'saeun_17', 'oings_2', 'kinda5exy', '_kyeore_', 'jero___95', 'm9721.j', 'kimhayeoni', 'myung_yu_mi', 'minhee_mini__', 'justin.j.here', 'min_nlog', 'luvofthesummer', 'lion_de_bebe', 'jinsolfit', 'luv_usagi35', 'limsss___', 'j__seok_p', 'laon_fitness', 'j_un13', 'junsoo_ceo777', 'kkkk2.24', 'jonikor_77', 'jihye_shin_', 'huit8siyeon', 'jeonju_leggings', 'jangddaeng._.e', 'jasmine.yeny', 'h_hyez', 'j_jjja', 'hsm990124_official', 'glambunny7', 'hotzzinie', 'hotsoongs', 'summerlike_insta', 'im_euuu', 'j.i.s_96', 'fobene_sport', 'helli_n2', 'ha__nulee94', 'fila_korea', 'grandeline.official', 'dewitfit_official', 'iknowjadestone_', 'errday_kr', 'dihye._.me_workout', 'bbopug', 'jeju1111111', 'amob___21', 'dalkomshoe2', 'aileen.kr', 'im_summer_fit', 'aari_nrin', 'harin_222', '_cindy_kim', 'hip_zzang', 'com.plex87', 'cipher.oh', 'elinacoco33', 'chic_z1zee', 'boreum_day', 'hyewon._.ni', 'hyunee_today', 'diet_mk858', 'be_fit_us', 'barbie_fit_', 'dear.beeni', 'aks1016ek', '_js081_0', 'chaewonfit', 'chaelook_limchaewon', 'zjy__yjz', 'ahavenof', 'yujunara', 'c_jxxjxx', 'yoonseo1181', 'yunaworld_sg', 'yoga_rihyun', '_quinzel_09', 'yeo._.uu', '_sinaeji', 'y8njin_01', '____mymimi', 'wintermoon_purple', 'cho_co_bin2', 'uni_choice1', '010_7676_0569_llll', 'toryhomepilates', '_46.10', 'sylvia_skyblue', '010_7676_0569_pppp', 'sso_omday', 'dailllly__looook', 'smileyujacha', '010_7676_0569_181818', 'sim9.6', '0416_remember', 'seeong_lee09_', 'hye__v0', 'dbwjdlena', '_babsohee', 'd.yun____', 'refuge_market', 'kg_eeeee', 'ssjj__1101', 'from_h38', 'huisoll', 'chloesdh', 'o____o.lee', 'mingzoee', 'bo_kyung__fitness', 'leylyly', 'min__________nim', 'jin_mom7838', 'luvbom_mom', 'yome_kim', 'lovelee100402', '_thesensegirls', 'lllllsuperstarlllll', 'yeon_._.zx', 'leegeumchae', 'yubeen__7', 'kimmly_booty', 'xxoeunvvn', 'jungmin.jane', 'cherr.ily', 'jjinnnnns', 'woody_n84', 'jety_look', 'y.ounjin', 'j_h_j__', 'threefour__34', 'i_m_dot', 'hong_tenniscoach_', 'sunkiki0', 'helon._.a', 'sujiq8', 'heavenpark', 'ssun422', '__yundaeng___', 'hwartist_sport', 'gahyun.e', 'spyder_suwon', 'fit_hyunjin', 'onyourd___owny', 'eunbi_market', 'secreetstudio_only_for_men', 'dokdo_munbanggu', 'hm.juliana_', 'betterline.official', 'pilla__min', 'define_sunn', 'saeromeee_', 'da.da_helena', 'like_honey___', 'cine_ryr', 'peng_giant', 'ch___425', '2.ayomm', 'blooming__jung', 'nahyun___p', 'black.buck_', 'iff_lovely', 'bboong2_com', 'miniqueen.ofqueen', 'beautique_global', 'jtaeyeon_', 'baby.lifter', 'lssunii', 'anyhorse_official', 'heidiroom39', '_woojung_lee', 'kimkingk0ng', '_hydemk', 'pilates_yumi_', '__hye_2', 'iwantyoursummer_official', '201._.sy', 'fashion365kr', '158_43_23', 'innxina', 'jjunakim', 'ann_mazhurnaya', 'hayong_jjjj', 'zzz.u_7', 'fitness_arena__official', 'heidi_ye0nji', 'agy.workout', 'young__.je', 'youngjinknit', '_pplum', 'you_lin_e', 'yoonble_love_', 'ham_with_pila', '_linaa_sp', 'yeonibaebae', 'yang__coach', '_bygracekim', 'woorish', 'want.enu_98', 'kyeong_yun_k', 'didrjf591', 'h_n_vly', '_a.bong', 'vickkygaga', 'thswldh_19', 'celebrity_fashion_kr', 'tae_khr', 'z2won_0423', 'beneunder_korea', 'aprovecha_al_max', 'yurana_market', 'seo_y_99', 'youngjoo_peach', 'amour_mond33', 'ye_ji_l', 'youngsuklee', 'workout_mingracle', '__parksieun', 'withmyl_', 'yeahzzang__', '7r0a_niiiii', 'ten.g__', 'forever.nyong', 'sulseam_jy', 'sujin_keen', 'starlight_mama_', 'ssj0806', 'dear_h.j', 'dew.e', 'ssomi015', 'soocong_fit']
    # user_infos_list = user_infos_list[200:]
    ##2. 유저 분할
    total_user_infos_group = divide_user_infos_list(user_infos_list, group_size=1)
    print(len(total_user_infos_group))

    ##3. db 발송
    send_total_message(total_user_infos_group, text, project_name=project, proxy=proxy)
