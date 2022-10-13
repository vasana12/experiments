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

    user_infos_list = ['coserygangnam', 'uberpilates_0222', 'dayayoga_studio', '_yoga_an_', 'yoga_theone', 'on_yoga_pilates_studio', 'yogabyotters', 'bbyoga_official', 'corehotyoga', 'americayoga_kundae', 'zenyogakorea', 'hotyogafly', 'yogabyhyun', 'thehotyoga', 'limeyoga27', 'yogi_tree_', 'americayoga_balsan', 'rose_yoga_ems_center', 'raanyoga_seoul', 'aywa_official', 'americayoga_gy', 'hongje.yogalight', 'yogalooks_seouldae', 'aymjyoga8080', 'americayoga_seoul', 'heayoga_mokdong', 'americayoga_yongsan', 'yoganpil0101', 'myoga_mapo', 'youryoga.flying', 'rose_yoga_pilates', 'ayo_ssja', 'nadiayoga_korea', 'shanti_aroma_yoga', 'americayoga_ewha', 'swarayoga_', 'omnibodyworkschungdam', 'flybungee_sungshin', 'yogastory_official', 'suryayoga_ceo', 'yoga_blossomm', 'ayo_yeouido', 'healing_u_5', 'americayoga_ds', 'aywa_official', 'yogatreeseoul', 'yoga.ilsang', 'ariass_2025', 'yoga_hae', 'blissyoga_smu', 'ityoga_junggye', 'americayoga__mokdong', 'eummyoga', 'iseonhyeon3', 'myoga_yj', 'delight_yoga1', 'inyoga55', 'yogafield_jn', 'weneed_yoga', 'sunyogastudio', 'aywa_official', 'myyoga_studio', 'ahimsa_yoga_meditation', 'ariayoga_seocho', 'muisyoga', 'withyogastudio', 'flyingyoga_in_newyork_bangbae', 'yogahaven.kr', 'life_is_practice', 'americayoga_wsn', 'worshipper_d', 'official.vihayoga', 'ratokyoga', 'yogarama_holistic', 'oneulyoga_pilates', 'flybungee_mapo', 'americayoga_sdmy', 'yogaroad_seoul', 'sabrina.yoga', 'laelyoga', 'miyoga_pilates_official', 'yoga8korea', 'artyoga__', 'lalayoga_seoul', 'flyingstory', 'o_yoga_studio', 'nadinyoga_', 'chaeun_yoga_studio', 'nru_yoga', 'americayoga_mia', 'jonggak_ypilatesnyoga', 'shantifulyoga_', 'sivanandayoga_seoul', 'americayoga_chch', '_oury_yogastudio', 'haru_yoga_pilates', 'sinchon_artyoga_pilates', 'yochamdal', 'yogastudio4242', 'zenyogakorea', 'l_yoga_balletfit', 'hyu_yoga', 'anushayogameditation', 'yoga_siwa_', 'aproyoga', 'hanayoga2221', 's.hot_yoga', 'jongwon_yogatherapy', 'vykorea', 'suki.usomyoga', 'today_yoga_pilates', 'yogavna_seoul', 'soulflow2021', 'jahayoga.lab', 'https:blog.naver.comwooodaob', 'feelyoga_pilates', 'yogabyhyun', 'larayoga_academy', 'inner_yoga_studio', 'hara__yoga', 'irai_yoga', 'yoga_nmore', 'ayjsyoga7271', 'g_yoga_pilates', 'flyingyoga_bird', 'yogawonderland_official', 'beyond_balsan', 'min.t_yoga', 'irisyoga_pilates_', '_reina.yoga_', 'eun_yoga', 'artyoga8279', 'yoga_asha', 'yoga5407783', 'ariayogamb', 'soom_yoga_', 'yeominbliss_seonjeongneung', 'yogastudio_boramae', 'jinhee7063', 'koo_yoga_place', 'daomyouga1219', 'susuyoga_', 'nainyoga', 'msyoga.sukchon', 'jaiyogameditation', 'hanhoyoga', 'yogasoop_studio', 'san.yoga_sokcho', 'Soonja.song', 'yoga_by_sun_', 'http:www.instagram.comililyoga', 'shim_yoga_studio', 'yoga.suna', 'cureyoga_official', 'ariayoga_wonju01041238512', 'choyi_yoga', 'sokcho_suyoga', 'jeiyoga', 'eastyoga.movement', 'soopyoga', 'yoga_flying_', 'ssom_yoga', 'http:instagram.comyoga_in_gangneung', 'YOGAHARU_WONJU', '7cindy0', 'yogahome_sokcho', 'ashtangayogachuncheon', 'haruyoga_pilates', 'yeva_yoga.pilates', 'yogahealpilates', 'tara_yoga1205', 'easy_yoga_', 'about.yoga_gangneung', 'yogahealpilates', 'yoga_heyou', 'meditation_korea', 'buddle_song', 'meditation_korea', 'oneyoga_sokcho', 'soom_yoga', 'd.o__yoga', 'maitri_gangneung', 'signature_yoga_pilates', 'marinecoreyoga', 'fitnessclub.jm', 'yoga_rania_575.0378', 'yongssam_pilates', 'yoga__forest', 'kyanayoga', 'balancingyoga_pilates', 'balancing_ildo', 'balancing_ara', 'jsy_yogapilates_official', 'yoga_raum_', 'premyoga_', 'thesyoga__hagwi', 'hamdeok_hatha', 'oryo_official_', 'drishtiyoga_official', 'jeju_arnayoga', 'yogawonderland_in_jeju', 'agastyogajeju', 'chuidasun_teahouse', 'jeju.yoga', 'unwind_yoga_jeju', 'aranya_yoga', 'soma_yoga_jeju', 'smilefit.hotyoga', 'jeju_yoganeul', 'yoga_12month', 'p.p.e.m', 'jeju_sadhana', 'jeju_pyoseon_yoga', 'hanumanyoga.saarah', 'biumyogaashram_jeju', 'suddha_yoga', 'lunayoga_pilates', 'jstudio0649031010', 'mi_yoga_pole', 'santos.ayoga', 'jeju_pranayoga', 'yoga_saenar', 'thebreathe_yoga', 'aahana_yoga', 'yogalabkorea', 'seogwipo_hara_yoga', 'yoga_y_jeju', 'nyasa_yoga_shala', 'thesyoga__hagwi', 'thesyoga_samhwa', 'wellbeing_yoga_meditation', 'meditation_korea', 'yoga_borom', 'gyanyogashram', 'jeju_yogajoy', 'hatha_amrita', 'yogahanaa', 'eka_jeju', 'meditation_korea', 'meditation_jeju', 'yoga_aewol', 'jeju_arayoga', 'http:instagram.comvalhallapoledance_jeju', 'bonyeon_yoga', 'jeju_shinji_zumba_yoga', 'daily_yogapilates?igshid=z0iyb846m8jg', 'lazymama_lounge', 'varanasi_jeju', 'mindfitness_inje', 'icorepilates.jeju', 'y.fitness_jeju', 'akasha_yoga_studio', 'coserysuwon', 'on_yogastudio', 'sooclinicyogacenter_wirye', 'allround_yoga', 'easyyoga_kg', 'yoga.spirit.flying.bungee', 'h_yoga_gh', 'yoga_bareum', 'zenyogakorea', 'newfit_yoga', 'kamyyoga', 'guri_bnb_yoga', 'lineholic_', 'shezyoga', 'danahan_yoga', 'goyohamyoga', 'lisayoga_master', 'yogada.aum', 'yoga_tes', 'aywa_official', 'oasis.yoga', 'reborn_yoga', 'zenyogakorea', 'studio.aum_official', 'yogazen_pila', 'yogastay', 'yoga.today_official', 'coseryujb', 'awesomebody2015', 'thehadastudio', 'yogastory_', 'yogahara2019', 'sunshineyoganbungee', 'omyoga1', 'ariayogadd', 'saraha_yoga', 'tao_jungdong', 'reborn_yoga', 'davi.yoga', 'vtm_yogapilates', 'm.s.m__yoga', 'inyoga8', 'thecalm_studio', 'adel_yoga77', 'gritmisa', 'dalcom_yoga_at', 'yogalowa_', 'oneyoga_shala', 'lahfit_flying', 'yoga_hrdaya', 'yoga__ashram', 'bomyoga.pilates_academy', 'oneyoga3014', 'kumkura_pm', 'kaiyyj', 'flying_miha', 'worshipper_d', 'danahan_yoga', 'staypilates', 'omyoga1?igshid=1c2vpm0hum2w8', 'hyoga_sj', 'yogaongi', 'yogatree_woonjung', 'peakbygym_segyo', 'yogageulim', 'yogathebom', 'dave_yogastudio', 'seocheon_yoga', 'ashtanga_yoga_bucheon', 'yoga_on_studio', 'y_flying_pt_bungee', 'bonnie_body', 'calm_yogastudio', 'yogabareun', 'danahan_yoga', 'flyingyoga_in_newyork', 'guri_ashtanga', 'harshi.yoga', 'gabayoga_kr', 'onhotyoga1', 'riatheyoga', 'yogagrit_yeokdong', 'satiyoga_kr', 'muditayoga_official', 'muditayoga_official', 'lizyoga_pilates', 'taoyoga_pilates_dongtan', 'soma_lk_yoga_pilates', 'aloka_yoga', 'lims_yoga', 'raonyoga_608', 'tristhana.yoga_official', 'premyoga_uijeongbu', 'sweetma.ma', 'larayoga_academy', 'moonflying_yoga', 'shy____shy', 'laksmiyoga2', 'jiya_yoga', 'yoga_237_', 'body_fit_yoga', 'flyingyoga_in_newyork_suwon', 'risa_icheonyoga', 'ilimyoga_with', 'cheongdam_ju_yoga_gym_official', 'yoga_mud', 'bhakti_flying_yoga_pilates', 'ashtangayogailsan', 'zenyogakorea', 'http:instagram.comyoga_studio.gg', 'ispoledance_official', 'yogagrit_official', 'bareumyoga', 'bepresent.yoga', 'padma_leesue', 'yoga_to_the_people', 'ashtanga_pearl', 'ceokjhhgs', 'nurisol.tree', 'yogavibe.studio', 'yogavida_studio', 'mj_studio8010', 'family_seasonyoga', 'bodhiyoga1555', 'larayoga_academy', 'clyoga_pilates', 'jinayogastudio', 'yoga_ratnaa', 'tina_yoga_pole_studio', 'ashtanga_karmayoga', 'ilsan_arium_yoga', 'jigum_yoga_studio', 'yoga.suna', 'yogafarm21', 'ilimyoga_with', 'mina__yoga', 'with_me_yoga_pilates', 'yoganpila_studio', '__yogadawn', 'yoga_rudha', 'minkyung_randa', 'seiyoung_ashtanga', 'hyoga_db', 'yoga_on_story?hl=ko', 'ashtanga.jennyyoga', 'yogaroom2244', 'flyingstory_yatop', 'ekayoga_studio', 'cl_yoga', 'yogadohban_yeon', 'mielyoga_', 'yoga_karuna_', 'sunmoonyoga_marie', 'goyo_yoga_', 'imyoga65', 'ilsan_hatha_yoga', 'ycrpilates', 'hae_moon_yoga', 'e__s__yoga_', 'me__yoga', 'sukhayamyoga', 'mukta_yogaone', 'patanjaliyoga_jecheon', 'yoga_zarak', 'viniyoga_daompilates', 'premyoga_cheongju', 'yogaroum_seolhee', 'jenayoga2018', 'yogaro_chungju', 'patanjaliyoga_dammashantiyoga', 'tania_yoga.pilates', 'trikona_yoga', 'a.lignyoga', 'j_able_yoga', 'j_able_yoga', 'marie_jiyoung81', 'ocean_river_yoga', 'yogarium', 'meditation_chungbuk', 'yoga_damru', 'yoga__bon', 'ashtangajennyyoga.jecheon', 'eveslave', 'marga___yoga_jecheon', 'yogaeun20', 'devishayoga', 'cha_yeon__', 'b.yoga__', 'yoga__rim', 'yogaonyou', 'ssong_yoga_pilates', 'savita_yoga', 'ceongjusoundyoga', 'vishuda_yoga', 'unme_yoga', 'okcheon_hathayoga', 'numujoayy', 'yoganr0701', 'shambodhi_yoga', 'hanulyoga', 'premyoga_cheongdang', 'karuna_gongju', 'premyoga_', 'yogamata2020', 'miracleyoga_minicafe', 'om._.yoga', 'indiyogapilates', 'jigeumyoga_official?igshid=13kauqsbz4b8s', 'dandayoga_', 'allthat_seosan', 'premyoga_sinbu', 'nalssinhanyoga_hj', 'yogapida', 'jung_flyingyoga_seosan', 'daisy__bodyfit', 'the_naeun_yogapilates', 'taoyoga_gyeryong', 'premyoga_asan', 'sh_therapy_yoga', 'premyoga_sseong', 'starhot_yoga', 'dangjinyogaacademy', 'yogakula_cheonan', 'yeosinyoga_dangjin', 'yoga.nanal', 'premyoga_boryeong?utm_medium=copy_link', 'premyoga_ssangyong', 'Prana_with_shanti', 'siestayoga9.500', 'hannayoga', 'day_yoga', 'yoga_royy', 'yoga_7246', 'lovelyoasis11', 'khj8658', 'yoga_pila_', 'saemteo_yoga', 'sujini4409', 'cheonan_bsyoga', 'yoga_yeohaeng', 'namuyogaweon', 'herbalife_oh', 'space.om_official', 'm_yoga_pt_asan', 'alwaysyoga4', 'boryeongashtanga_official', 'star_greeting.yoga', 'bodypalace__gym', 'haenam.yoganlife', 'hiranya_yoga', 'dipika_yoga', 'dailybodyfit_wall', 'dawoomyoga', 'dawoomyoga', 'ipurple209', 'oneul_yoga', 'sba9004', 'yoga__sum', 'yogaharu_yeosu', 'yangyujeong_lilayoga', 'mandarin_yoga_lab', 'vanessa__yoga', 'samadhiyoga_studio', 'dawoomyoga', 'yudal_yoga_pilates', 'joyananda_yoga', '4yoga_yjyj', 'ayus_yoga_', 'stay_yogastudio', 'yoga_bhagya', 'merry_yoga_', 'Surya_yoga_dam', '4yoga_gd', '4yoga_changduk', 'nicedayoga', 'retreat_wall_yoga', '4yoga_yjyj', 'dhyan_yogapila', 'be_um_yoga', 'hye_yoga_', 'my._.yoga', 'jflyingyoga', 'yogahouse201', 'mokpohathayoga', 'yeosu_bareun', 'hosuyoga_official', 'satyananda_yoga_ashram_korea', 'yogamanaaum', 'medi_yoga', 'yoga_forrest', 'bichae_yoga', 'nadi.saem', 'heyumyoga_suncheon', 'withmeyoga', 'gj.prana_yoga', 'therimyoga', 'mystudio__official', 'we.me_yoga1', 'yoga.space_of_mind', 'bandha_yoga', 'balance__yoga', 'yangsuryeon4', 'daon_yoga_hg', 'conversant_yoga_medical', 'nilah._.yoga', 'gkxkdyrk', 'aranya_mediyoga', 'yoga.ae_', 'y_flying_bungee', 'dianayoga0544762226', 'miyoga_gyeongju', 'bogyeong_moment', 'yogastudio_ongi', 'yoga.suum', 'yoga_soopia_pilates', 'inhae_yoga', 'j_aerial_yoga', 'yoon_yoga_', 'premyoga_gumi', 'braintr_zzang', 'balanceyoga__pilates', 'yogasoul_korea', 'ahinyoga_pilates', 'neulyoga.gumi', 'lilayoga_official', 'yogasis_official', 'breathe.in.yoga', 'yujyoga1', 'yogarosalim', 'raum1908', 'jejungwon6556', 'yogaayur3578', 'yogasis_official', 'innerside_yoga', 'miyogabungeeflying', 'gumi_hatha', 'baegsoyeon9548', 'yoga._.om', 'yoon_yogastudio', '0yogalife0', 'zentherapy_gyeongsan', 'mihwa.jang', 'o_da_fit', 'freyayoga3733', 'mimiyoga_baby', 'imyoga0', 'yangsuryeon4', 'weonhyoju53', '_yoga_yeon', 'yoganeul_', 'torayogastudio', 'today__yoga', 'happy_yogapila', 'yoga_in_stay', 'warmmindyoga_official', 'ejyoga_', 'sm_yo_ga', 'bera7030', 'yoga_dance_9', '_jung_yoga', 'bht_yogapila', 'yoga.pilates053.953.6780.6781', 'thejungle_yogaforest', 'malayoga_gumi', 'aehyun0323', 'dahn_yoga', 'malgeum.studio', 'studiosu517', 'yogaplanet_', 'atha_yogapilates', 'yogatheall', 'pejblue2', 'yoonefit', 'yoga.danda', 'premyoga_gimhae', 'rudra_magic', '_jinyogapilates', 'changwonyoga', 'yogini_ganesha', 'seminsuk_yoga_center', 'prana_yoga_pilates_', 'taoyoga_jinju', 'line__0102?igshid=e5wes9ri8cxr', 'lownyoga', 'lown_yoga_roo', 'you1_yoga', 'karmayoga_ashtanga', 'aju_gooddayyoga', 'vip.yogapilates.buk', 'agni_yoga__pilates3', 'yogadabansa', 'navi_yoga', 'alive_yoga_', 'namaste_yogapilates', 'leanbody_pilatesyoga', 'dhira_yoga_', 'ieumyoga', 'yogaom_hatha', 'changwon_hatha', 'wall.yoga', 'yoga_school_leeashram_geoje', 'ganga_yoga', 'lamedestudio', 'haman_shanti_yoga', 'parkeunhye7021', 'nayoung_yogaclass', 'ingi_flying_bungee', 'beluga91love', 'hari___yoga', 'amanda_flying_yoga', 'danibaba_yoga', 'aliveyoga_2', 'yoga_achaha', 'yoga__marga?igshid=1dl3vs428u4uy', 'ashtanga_jungmihyeyoga', 'nadi_yuj', 'young_pilates_yoga', 'rishiyoga_om', 'ballyyoga', 'ganga_yoga', 'india_yoga_gimhae', 'yogarim__', 'adeline_pilates_n_yoga', 'gc_yuj_studio', 'ashtanga_jinju', 'your_flying_yoga', '4yoga_', 'yoga.zip', '2den__2', 'newbeborn_', 'meditation_kyungnam', 'yeonjoo__yoga', 'yoga_berry_', 'soulstudio_changwon', 'satcitnanda_yoga', 'heeyoonyoga_studio', 'yogatheaum_', 'yoga_pilates_gimhae_', 'limja1004', 'sujan_yoga_studioty', 'c_oz__y', 'handsilvermouse_yoga', 'hyoga_7965', 'cumcuneun66', 'gangayoga2020', 'supmyeongsangdeurim', 'booroo02', 'jaunsunga', 'hatha_gomyoga', 'dongpirangyoga', 'banilra', 'meditation_kyungnam', 'samwonenergy', 'imoneness', 'selfrealization__coach', 're_body_dance_fitness', 'shineunju0327', 'premyoga_dunsan', 'wingshot_yoga', 'caeum_yoga', 'lenayogapilates', 'taoyogatanbang', 'dhyana_rin?igshid=k0mu2yb98btn%22', 'yoganeul', 'movement_yoga_pilates', 'taoyogagwanpyeong', 'minkyungdon', 'bonyoga_dj', 'yoga_neuruwon', 'hiyoga_studio_', 'sujin.yoga', 'yogasol_pilates1', 'subinyoga_daejeon', 'yoga_plus_', 'yoga_jeonmin', 'yogaon_official', 'therapy_yogakim', 'lunayoga_daejeon', '_joy_yoga', 'ohpila_yoga', '__commayoga2', 'ashtanga.yogapilgrim', 'sohot_yoga', 'therapy_yogakim', 'idyoga__', 'yogaro_', 'yoga_academy_042_544_4424', 'parkbojungyoga', 'wings_yoga1228', 'taoyoga_noeun_', 'dawon_pilates_songchon_', 'newcmp_yogaholic', 'nirvanayoga_korea', 'pilatesforukr', '_todayyoga_', 'cs_master_lisa', '__commayoga', 'wall__yoga', 'madebyme2019', 'more.rest.yoga', 'yogamoons7', 'janny._.k', 'yang_jiyun_', 'soomshim_yoga__official', 'yoga_beingmyself', 'yoga.hae', 'yogaram_', 'yogavna_daejeon', 'meditation_korea', 'yoga_yeonda', 'vaira_yoga', 'thenamu.yoga', 'sunshine_yoga8338', 'meditation__diary', 'meditation_korea', 'daejeon_goodball', 'meditation__diary', 'brain_meditation_wolpyeong', 'yoga_healience', 'greenrhythm.kr', 'soundbathkorea', 'nisarat_business', 'taoyoga_jongchon1', 'memd1004', 'anandayoga_dagym', 'daily.1359', 'me_yoga_pilates', 'isis_yoga_pilates', 'taoyoga_saerom', 'prajna_yoga_sejong', 'seo.a.kim', 'asio_yoga_', 'bareunyoga', 'at.awake', 'asioyoga', 'yogananum', 'bareun_meditation', 'ymh_yoga_meditation', 'meditation__diary', 'mysorefitness_official', 'artistic__yoga', 'asyuram_yoga', 'dalri_yoga', 'deline_studio_', 'prana._.yoga', 'llama_yoga_', 'bodynsoul.yulha', 'ayurveda_yoga_kr', 'shamata_yoga_daegu', 'yoga.pilates053.953.6780.6781', 'beyoum_053.744.7440', '@yoga_haang', 'rajahatha486', 'yaeseomyoga', 'lynseo3020', 'my_yoga_flying', 'yoga_smilefit', 'mooahyoga_studio', 'the303flyingyoga_official', 'yesyoga_lily', 'yogazen_flyingyoga', 'yoga_by_yoon', 'thanq_yoga', 'gain_pilates_yoga', '#h_yoga_studio', 'mayayoga92', 'in.and.yoga', 'irinayoga_', 'jay_yoga_', 'beyoum_yoga?igshid=nkstf7p6fjde', 'wellness_j_yogi', 'suriya_yoga_', 'bhishmayoga', 'gidwk1285', 'explorelocations183586625493141', 'anyunheeyoga_pilates', 'themeyoga_', 'bodybalance_songhyun', 'hope.yoga_pilates', 'addiyogapilrateseu', 'jung_mediyoga', 'samadhi_hatha', 'yoga_pilates_h_20', 'balanceyogapila', 'anjaliyoga__daegu', 'kang_tae__yang', 'yaeseomyoga', 'balance_yoga.pilates', 'leela_yoga_pila', 'daegu_yoga10000', 'yogaplanet_', 'premyoga_', 'yeon_yogapila_official', 'coreyoga_pilates', 'smileyoga_fit_pilates', 'lovely85298', 'yogazip', 'ridiayoga_rani', 'yogaday_3939', 'rayyoga_minjung', 'yoga_haang', 'yogapilates_master', 'ayh_yoga_pilates', 'beautiful_y_o_g_a', 'gyoga11', 'goodball_daegu', 'leeseunghyun_yoga', 'saydotong21', 'baradeon__', 'ajnajieun', 'mie_yoga', 'hyeonpung_yoga', 'my_yoga_flying', 'meditation_korea', 'reset_yoga_pilates', 'pungyo1', 'yogane_samdeok', 'damyeon_yoga', 'samwonenergy', '5sheisvip_11vippilates', 'yoga6155', 'coserysamsan', 'lsj_yoga', 'bsyoga_meditation_official', 'jungjunghe0110', 'yogaharu_studio', 'shiny_yogastudio', 'daomyogapilates', 'bori__yoga', '902_S_yoga', 'imin_yoga', 'bhavayoga.studio', 'lsj_yoga', 'heal_yogaa', 'leeinseung_yoga', 'raun_yoga.boderaun', 'tristhana.yoga_official', 'hamsa_yoga1130', 'myown__yoga?utm_medium=copy_link', 'garbhayogastudio', 'teraon_yoga_', 'rrrrai_yoga', '@yogabeyond_ulsan', 'aiemhasyoga', 'yoga_01098119989tagged', 's_m_j8446', 'choi_geonhuiyogacenter', 'dajung_shala', 'primulahotyoga', 'siwon_yoga', 'marciamisolee', 'greena_ye', 'taoyoga.ulsan', 'aricea_yoga', 'aromayogalila', 'hariyogapilates', 'meditation_korea', 'yoga_prema22', 'bsyoga_maegok', 'jnana_yoga_ulsan', 'yogabeyond.official', 'yoga_sushumna_', 'jyoga_studio', 'zentherapy_ulsan', 'k_meditation_dahnworld', 'ddeul_yoga__', 'soyeon6378', '_yoga_krsna_', 'soon.yoga_', 'shes_yoga', 'yoga_muse_', 'body_balance_school_', 'goyo_ga', 'yogavna_online', 'agniyoga_97', 'yoganomad_official', 'appleyoga7920', 'yogayolife', '__meandyoga', 'ashtangayoga.dawon?utm_source=ig_embed&ig_rid=fed32e88-2e80-475f-a4dc-0eb6eccc723e', 'yogabliss', 'a.n.v_pilates', 'yogadaumm__pilates', '_layayoga', 'inyoga_pilates', 'ddp_onyogapilates', 'sherpainkorea', 'the_flow_studio', 'insoulyoga', 'mahatyoga2021', 'seh7979', 'atisayoga_official', 'manoayoga_leeeunhui', 'woosom_', 'busan.yogaindia', 'suna_yoga', 'yogaflexdansin', 'therapy.yoga', 'raon_yoga_pole', 'yogaharin', 'medical_yoga_', 'irisyoga_pilates', 'anahatakorea', 'lara_yogapilates_', 'meditation_truemind', 'medi_han_yoga', 'hannayoga_healing', 'meditation_haeundae', 'lunasium144', 'yogav_jangsan', 'yoga.soom', 'meditation_hwamyeong', 'busan_bonyoga', 'yoganamu_busan', 'anahatayoga_house', 'daeyeon.dahn', 'busanmeditation', 'meditation_dangri', 'meditation_korea', 'yoga_bom_', 'yogabam_', 'hyijeong6037', 'yoga_pilates_one', 'jhkim435', 'yoga_place_d', 'meditation_minam', 'meditation_korea', 'donggyeong_yoga', 'yoga.paramita', 'rigyeong.i', 'atma_yoga_ashram', 'bodylineflyingyoga_official', 'bodyforminds', 'yogasaem', 'ruhen_yoga.pilates', 'jinhee_yoga_studio_', 'yoga_gyeol', 'cureyoga', 'thebetteryogapilates', 'nalyo_bonnyfit_go', 'taoyoga_dongsan', 'theyoga_kunsan', 'narsh_yoga', 'the_centum', 'line5434455', 'oneul_yoga_', 'nalyo_noble', 'taoyoga___mohyeon', 'luna.c_yoga?utm_medium=copy_link', 'yuj_yoga_', 'taoyoga_jeonju', 'nalssinhanyoga_love', 'yogakaruna2020', 'querencia_yoga', 'agniyoga_hata?igshid=YmMyMTA2M2Y%3D', 'anwoohyang', 'gunsanyoga_jinyoga_jinpilates', 'nalssinhan_yoga', 'yogaacademy_gimje', 'bodyfityoga_bom', 'korean.chou.yogi', 'nalyo_3000', 'taoyoga_pyongwha', 'fityogates', 'triyoga_jeonju', 'anandayoga2020', 'yoga.haru', 'elyogagym', 'nyyoga0903', 'caribbean1007', 'yoga__soom', 'yoga_yuna_pilates', 'hayeon__yoga', 'mafitcare', 'tanz_yoga', 'tanz_yoga', 'soom.yoga', 'yoga.bewitch', 'yogar0ma', 'young___yoga', 'welmommyoga_official', 'ssooongmin', 'b.b_terra', 'nani_crochet_yoga']
    ##2. 유저 분할
    total_user_infos_group = divide_user_infos_list(user_infos_list, group_size=1)
    print(len(total_user_infos_group))

    ##3. db 발송
    send_total_message(total_user_infos_group, text, project_name=project, proxy=proxy)
