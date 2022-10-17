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
host, port, proxy_username, proxy_password = "resi3.ipb.cloud", "9000", "MrIlCvzYImHc0I3t", "wifi;us;;;;"
# host, port, proxy_username, proxy_password = "resi3.ipb.cloud", "9000", "AX7S3xZk5L9RF1So", "wifi;us;;;;"
proxy = f"http://{proxy_username}:{proxy_password}@{host}:{port}"

max_login_try_num = 2
max_messages_per_day = 100
max_group_size = 30


def infinite_login(client: Client, username, max_messages_per_day, client_name=None, session_id=None, proxy=None):

    while True:
        ##1. 사용할 계정 DB 에서 가져오기
        account_setting_info = select_user(username=username, client_name=client_name, max_messages_per_day=max_messages_per_day)

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
    project = "ballet_insta_1"

    project_start_date = "2022-10-13"

    text = get_dm_source.get_source_message(f"{project}.txt")
    # user_infos_list = user_split("""""")
    # print(user_infos_list)
    # input()

    user_infos_list = ['_todayyoga_', 'cs_master_lisa', '__commayoga', 'wall__yoga', 'madebyme2019', 'more.rest.yoga', 'yogamoons7', 'janny._.k', 'yang_jiyun_', 'soomshim_yoga__official', 'yoga_beingmyself', 'yoga.hae', 'yogaram_', 'yogavna_daejeon', 'meditation_korea', 'yoga_yeonda', 'vaira_yoga', 'thenamu.yoga', 'sunshine_yoga8338', 'meditation__diary', 'meditation_korea', 'daejeon_goodball', 'meditation__diary', 'brain_meditation_wolpyeong', 'yoga_healience', 'greenrhythm.kr', 'soundbathkorea', 'nisarat_business', 'taoyoga_jongchon1', 'memd1004', 'anandayoga_dagym', 'daily.1359', 'me_yoga_pilates', 'isis_yoga_pilates', 'taoyoga_saerom', 'prajna_yoga_sejong', 'seo.a.kim', 'asio_yoga_', 'bareunyoga', 'at.awake', 'asioyoga', 'yogananum', 'bareun_meditation', 'ymh_yoga_meditation', 'meditation__diary', 'mysorefitness_official', 'artistic__yoga', 'asyuram_yoga', 'dalri_yoga', 'deline_studio_', 'prana._.yoga', 'llama_yoga_', 'bodynsoul.yulha', 'ayurveda_yoga_kr', 'shamata_yoga_daegu', 'yoga.pilates053.953.6780.6781', 'beyoum_053.744.7440', '@yoga_haang', 'rajahatha486', 'yaeseomyoga', 'lynseo3020', 'my_yoga_flying', 'yoga_smilefit', 'mooahyoga_studio', 'the303flyingyoga_official', 'yesyoga_lily', 'yogazen_flyingyoga', 'yoga_by_yoon', 'thanq_yoga', 'gain_pilates_yoga', '#h_yoga_studio', 'mayayoga92', 'in.and.yoga', 'irinayoga_', 'jay_yoga_', 'beyoum_yoga?igshid=nkstf7p6fjde', 'wellness_j_yogi', 'suriya_yoga_', 'bhishmayoga', 'gidwk1285', 'explorelocations183586625493141', 'anyunheeyoga_pilates', 'themeyoga_', 'bodybalance_songhyun', 'hope.yoga_pilates', 'addiyogapilrateseu', 'jung_mediyoga', 'samadhi_hatha', 'yoga_pilates_h_20', 'balanceyogapila', 'anjaliyoga__daegu', 'kang_tae__yang', 'yaeseomyoga', 'balance_yoga.pilates', 'leela_yoga_pila', 'daegu_yoga10000', 'yogaplanet_', 'premyoga_', 'yeon_yogapila_official', 'coreyoga_pilates', 'smileyoga_fit_pilates', 'lovely85298', 'yogazip', 'ridiayoga_rani', 'yogaday_3939', 'rayyoga_minjung', 'yoga_haang', 'yogapilates_master', 'ayh_yoga_pilates', 'beautiful_y_o_g_a', 'gyoga11', 'goodball_daegu', 'leeseunghyun_yoga', 'saydotong21', 'baradeon__', 'ajnajieun', 'mie_yoga', 'hyeonpung_yoga', 'my_yoga_flying', 'meditation_korea', 'reset_yoga_pilates', 'pungyo1', 'yogane_samdeok', 'damyeon_yoga', 'samwonenergy', '5sheisvip_11vippilates', 'yoga6155', 'coserysamsan', 'lsj_yoga', 'bsyoga_meditation_official', 'jungjunghe0110', 'yogaharu_studio', 'shiny_yogastudio', 'daomyogapilates', 'bori__yoga', '902_S_yoga', 'imin_yoga', 'bhavayoga.studio', 'lsj_yoga', 'heal_yogaa', 'leeinseung_yoga', 'raun_yoga.boderaun', 'tristhana.yoga_official', 'hamsa_yoga1130', 'myown__yoga?utm_medium=copy_link', 'garbhayogastudio', 'teraon_yoga_', 'rrrrai_yoga', '@yogabeyond_ulsan', 'aiemhasyoga', 'yoga_01098119989tagged', 's_m_j8446', 'choi_geonhuiyogacenter', 'dajung_shala', 'primulahotyoga', 'siwon_yoga', 'marciamisolee', 'greena_ye', 'taoyoga.ulsan', 'aricea_yoga', 'aromayogalila', 'hariyogapilates', 'meditation_korea', 'yoga_prema22', 'bsyoga_maegok', 'jnana_yoga_ulsan', 'yogabeyond.official', 'yoga_sushumna_', 'jyoga_studio', 'zentherapy_ulsan', 'k_meditation_dahnworld', 'ddeul_yoga__', 'soyeon6378', '_yoga_krsna_', 'soon.yoga_', 'shes_yoga', 'yoga_muse_', 'body_balance_school_', 'goyo_ga', 'yogavna_online', 'agniyoga_97', 'yoganomad_official', 'appleyoga7920', 'yogayolife', '__meandyoga', 'ashtangayoga.dawon?utm_source=ig_embed&ig_rid=fed32e88-2e80-475f-a4dc-0eb6eccc723e', 'yogabliss', 'a.n.v_pilates', 'yogadaumm__pilates', '_layayoga', 'inyoga_pilates', 'ddp_onyogapilates', 'sherpainkorea', 'the_flow_studio', 'insoulyoga', 'mahatyoga2021', 'seh7979', 'atisayoga_official', 'manoayoga_leeeunhui', 'woosom_', 'busan.yogaindia', 'suna_yoga', 'yogaflexdansin', 'therapy.yoga', 'raon_yoga_pole', 'yogaharin', 'medical_yoga_', 'irisyoga_pilates', 'anahatakorea', 'lara_yogapilates_', 'meditation_truemind', 'medi_han_yoga', 'hannayoga_healing', 'meditation_haeundae', 'lunasium144', 'yogav_jangsan', 'yoga.soom', 'meditation_hwamyeong', 'busan_bonyoga', 'yoganamu_busan', 'anahatayoga_house', 'daeyeon.dahn', 'busanmeditation', 'meditation_dangri', 'meditation_korea', 'yoga_bom_', 'yogabam_', 'hyijeong6037', 'yoga_pilates_one', 'jhkim435', 'yoga_place_d', 'meditation_minam', 'meditation_korea', 'donggyeong_yoga', 'yoga.paramita', 'rigyeong.i', 'atma_yoga_ashram', 'bodylineflyingyoga_official', 'bodyforminds', 'yogasaem', 'ruhen_yoga.pilates', 'jinhee_yoga_studio_', 'yoga_gyeol', 'cureyoga', 'thebetteryogapilates', 'nalyo_bonnyfit_go', 'taoyoga_dongsan', 'theyoga_kunsan', 'narsh_yoga', 'the_centum', 'line5434455', 'oneul_yoga_', 'nalyo_noble', 'taoyoga___mohyeon', 'luna.c_yoga?utm_medium=copy_link', 'yuj_yoga_', 'taoyoga_jeonju', 'nalssinhanyoga_love', 'yogakaruna2020', 'querencia_yoga', 'agniyoga_hata?igshid=YmMyMTA2M2Y%3D', 'anwoohyang', 'gunsanyoga_jinyoga_jinpilates', 'nalssinhan_yoga', 'yogaacademy_gimje', 'bodyfityoga_bom', 'korean.chou.yogi', 'nalyo_3000', 'taoyoga_pyongwha', 'fityogates', 'triyoga_jeonju', 'anandayoga2020', 'yoga.haru', 'elyogagym', 'nyyoga0903', 'caribbean1007', 'yoga__soom', 'yoga_yuna_pilates', 'hayeon__yoga', 'mafitcare', 'tanz_yoga', 'tanz_yoga', 'soom.yoga', 'yoga.bewitch', 'yogar0ma', 'young___yoga', 'welmommyoga_official', 'ssooongmin', 'b.b_terra', 'nani_crochet_yoga']
    ##2. 유저 분할
    total_user_infos_group = divide_user_infos_list(user_infos_list, group_size=1)
    print(len(total_user_infos_group))

    ##3. db 발송
    send_total_message(total_user_infos_group, text, project_name=project, proxy=proxy)
