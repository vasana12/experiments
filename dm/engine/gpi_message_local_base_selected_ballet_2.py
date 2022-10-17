# -*- coding: utf-8 -*-

import json
import math
import sys
import requests
import time
from dm import config
from dm.engine.gpi_auth import login_v_gpi, login_by_sessionid_v_gpi, select_user
from dm.engine.user import user_split, divide_user_infos_list
from instagrapi import Client
from instagrapi.types import User
import logging
from instagrapi.types import DirectMessage
from instagrapi.exceptions import UserNotFound, ClientForbiddenError, ClientError
from db import m_instagram
from db.model import *
from dm.engine import completed_target_influencer
from dm.engine.exceptions import *
from dm.execute.run_select_influencer import get_influnecer_info_by_project, search_influencer_info, \
    get_influnecer_user_id_by_project
from dm.prepare import get_dm_source, get_influencer
from dm.engine.gpi import get_user_id_by_username_rapid_api, get_user_by_id_lamadava, get_user_by_id_gpi, \
    get_user_id_by_db

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

max_login_try_num = 2
max_messages_per_day = 100
max_group_size = 30


def infinite_login(client: Client, username, max_messages_per_day, client_name=None, session_id=None, proxy=None):

    while True:
        ##1. 사용할 계정 DB 에서 가져오기
        account_setting_info = select_user(username=None, client_name=client_name, max_messages_per_day=max_messages_per_day)

        if account_setting_info is None:
            logger.error("사용가능한 계정이 없습니다 infinite login 을 종료합니다.")
            raise AccountException

        ##2. 가져온 계정으로 로그인 시도. session 받아오기
        if session_id:
            login_session = login_by_sessionid_v_gpi(client, session_id)
        else:

            login_session = login_v_gpi(client, account_setting_info["username"], account_setting_info["password"])


        ##2.1 가져온 계정으로 로그인이 성공한 경우 받아온 session을 return 해준다
        if login_session:
            account_setting_info.update(graph_session=client.sessionid)
            return account_setting_info

        ##2.2 가져온 계정으로 로그인이 실패한 경우 계정을 새로 가져온다.
        else:
            continue


def get_valid_user_ids(user_ids):
    valid_user_ids = []
    for user_id in user_ids:
        try:
            valid_user_id = get_user_by_id_gpi(user_id, proxy)
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

                client = Client()
                client.set_proxy(dsn=proxy)
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
                if account_retry_num >= max_account_retry_num:
                    raise AccountRetryExcessException

                client = Client()
                client.set_proxy(dsn=proxy)
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
        completed_target_influencer.push_influencer_completed(project_name=project_name, start_date=project_start_date,
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
    project = "ballet_insta_2"

    project_start_date = "2022-10-13"

    text = get_dm_source.get_source_message(f"{project}.txt")
    # user_infos_list = user_split("""""")
    # print(user_infos_list)
    # input()

    user_infos_list = ['ablanc_ballet_balsan', 'yun.balletfit', 'ballet.ba', 'reverence_ballet', 'daon_dance', 'sejong_kiwoom_ballet', 'balletdebon', 'etoile_ballet_academy', 'muse_yeouido', 'balletfitness_mullae', 'pina_dance_station', 'rang_ballet_studio', 'medora05', 'balletlemang7', 'bgdance_yeouido?igshid=sv8zg3y99zzs', 'mio.ballet_', 'lumiere202009', 'sa_ballet_academy', 'vien_ballet', 'jewballet', 'ewha_sejong', 'theswanballet', 'balletontop', 'muyongnara66', 'maeenballet', 'knb_ballet_gimpo', 'sum_art_studio', 'elegance_ballet_academy', 'sejong__academy', 'gounsun_ballet_yoga', 'theswanballet', 'yangjuhee__dance', 'laruedeballet', 'yimazinebox', 'dari_bridge', 'k.gyunaballet', 'a.r_ballet', 'yu_byeol82', '_coco.ballet', 'elledanse_official', 'lunadanceacademy2017', 'the_k_ballet', 'seulart_ballet_academy', 'ondine.dance', 'sejongnoble', 'yoos.ballet', 'barreinabag', 'jominhee_ballet', 'kirov_ballet_academy', 'sejongshineballet', 'reve_ballet_', 'sunyoga_ballet_pilates', 'swanballet_academy', 'jireh_dance', 'the_beauty_ballet', 'adella_k17', 'sooballe', 'reina_ballet_academy', 'ssooongmin', 'gounballetfit?utm_medium=copy_link', 'yein_ballet', 'yein2018', 'incheon.royal', 'la_beaute_ballet_academy', 'grand_ballet_incheon', 'sw_jun_ballet', 'lereve.ballet', 'doing35', 'ornan_1004', 'songdobolshoiballet', 'ballet_jh', 'ewhalala', 'briller_art_dance_company', 'newballet_academy', 'house.ballet', 'seochanglausanne', 'lilededanse', 'twostephall_official', 'artdockdance_studio', 'balletplus_ballet', 'tutu_ballet_', 'dodo_dance_hall', 'balletnco_w', 'billy_bodyfit', 'r.se_dance', 'the_ballarepil_seoul', 'balletdefirstige', 'move.mua', 'bliss_ballet', 'bns_ballet', 'totoballet_official', 'ballet_castle', 'balletomane_bangbae', 'banpoballetacademy', 'ybckorea', 'oyjballet', 'aliceballet1', 'the_royalballet', 'kbec_ballet', 'and_____you', 'yballet1', 'b_ballet_seoul?hl=ko', 'jini_studio_2', 'starballet_academy', 'odette.ballet', 'liberty_ballet', 'khg_ballet', 'ewhashushu_helio', 'la_vie_ballet', 'jeesballet', '1step_studio', 'rinanoballet', 'seouldanceacademy', 'grande_ballet', 'passaggio_dance', 'yula_ballet', 'ballet_ro', 'silhouette_pole_studio', 'pole.flower__official', 'yejongpointeballet', 'with_ballet', 'dance.spaceroom30', 'museballet_official', 'amigoballet_apgujeong', 'allthatballet', 'insideballet', 'modernstage123', 'balletshoe_official', 'elline_ballet_', 'balgronie_official', 'as_body_', 'choihyejin_dance', 'balletfit_korea', 'lalitosoom_official', 'bns_ballet', 'lballet_samsung', 'antte_balletfit', 'antte_balletfit', 'h_dance2019', 'theballetacademy_seoul', 'dearheal_theballet', 'limjiyoung.ballet', 'HealingPoledance', 'the1stballet', 'arts_et_dance', 'c.m.r.ballet', 'swanballet_studio_s', 'balletfit_korea', 'flowfellow_official', 'reballet_', 'laviede_danse', 'venus_ballet', 'luneballet', 'sillim_sda_', 'wangzyroyalballet', 'yuri_ballet_studio', 'salon_de_ballet', 'yang_studio88', 'lapose_ballet_academy', 'somebody_tanz_studio2', 's2barredance', 'eba_yejongeliteballet', 'yj_etoileballet_wirye', 'miline_ballet', 'ablanc_ballet', 'brillanteballet_', 'miline_ballet', 'namdancecompany', 'rael.79', 'a_better_dance', 'vaganovabd', 'sharondance_', 'pilates_pc', 'the_balletfitstudio_official', 'jblancballet', 'sharondance_anyang', 'yeonpolestudio', 'lunaballet_sj', 'enpointeballet_kr', 'pium_dance', 'sejongtop_dance_school', '_dance_ran', 'body_.memoria', 'and_____you', 'balletdegarden', 'nisarat_business', 'mare_ballet', 'lareveballet', 'chouette_liseballet', 'etoile_ballet_dasan', 'karts_tanz', 'yangsoyeong802', 'dplace_official']
    ##2. 유저 분할
    total_user_infos_group = divide_user_infos_list(user_infos_list, group_size=1)
    print(len(total_user_infos_group))

    ##3. db 발송
    send_total_message(total_user_infos_group, text, project_name=project, proxy=proxy)
