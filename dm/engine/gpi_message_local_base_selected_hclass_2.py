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
        account_setting_info = select_user(username=username, client_name=client_name, max_messages_per_day=max_messages_per_day)

        if account_setting_info is None:
            logger.error("사용가능한 계정이 없습니다 infinite login 을 종료합니다.")
            raise AccountException

        ##2. 가져온 계정으로 로그인 시도. session 받아오기
        # session_id = account_setting_info["session"]["sessionid"]
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
            valid_user_id = get_user_by_username_lamadava(username)
            # valid_user_id = get_user_by_id_gpi(user_id, proxy)

            # valid_user_id = get_user_id_by_username_rapid_api(username)
            # valid_user_ids =
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
                if e.__class__.__name__ == "ChallengeRequired":
                    INSTA_ACCOUNT_OBJ.account_collection.update_one({"username": account_info["username"]},
                                                                    {"$set": {"status": "unavailable"}})
                if account_retry_num >= max_account_retry_num:
                    raise

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

                if e.__class__.__name__ == "ChallengeRequired":
                    INSTA_ACCOUNT_OBJ.account_collection.update_one({"username": account_info["username"]},
                                                                    {"$set": {"status": "unavailable"}})
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
        time.sleep(7)
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
            logger.info(f"count_send_message: 총 {count_send_message}개의 DM 발송")

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
    project = "hclass_5"

    ##파일이름
    filename = "hclass"
    project_start_date = "2022-11-03"

    text = get_dm_source.get_source_message(f"{project}.txt")
    user_infos_list = user_split("""""")
    print(user_infos_list)
    user_infos_list = ['anjiisgood', 'ah_girlss', '_y0uhee', '_k.k_mii', '_hye77', '_an_thaway_', '__yun_jung', '__na.yeon_', '__veronica.k', '22_hyun2', 'altongsj', 'rumi_do_', 'milkywei_lady', 'myeong__zi', 'evelyn.o_h', 'sol.ookbook', 'seoyoung_170', 'xxox_xox', 'bba_na_na', 'audrey_._lee', 'thelife_leader', 'rosa.co.kr', '10h27m', '_169nana', 'mingki_89', 'zzo.romee', 'yoonbly_98', 'yeoniry', 'weostudio', 'wdfit.min', 'themostfit_hyun', 'swim_danbi', 'sseo_y9', 'sol___ip', 'sj__inyvr0327', 'shine181201', 's_hyejinss', 'ppeum__vely', 'myongstar_1', 'luha_unni', 'juvely.94', 'jo11_15', 'jamonjamon95', 'infit_battery', 'hko92', 'highfive_gym_manager', 'feckenlovely', 'ella__0705', 'dini.world', 'chaerry_berry', 'bodygraphy__kim', 'beckysj_', 'a_armye_e', '__fimi_feel__', '1_sell_0', 'adora_bin_', 'melove_93', 'kimmiso3', 'yujiyuji1117', '_still.your', 'cchvvnn', '_.chorong._', 'champion_wanjung', 'yun_ahri', 'mj_07.18', 'yuna.jeon', 'yu_lim_95', 'whatever_office', 'thflrkd1119', 'spring_of_hermione', 'song_hyehyun', 'sae_vom_', 's_o_zzin', 'ra.en_waxing', 'pt_elf___', 'poledancer_ellycat', 'pitta_somiiday', 'physique_winnie', 'padammin', 'nari.camila', 'madinforyou', 'machenoki', 'k__jinsol', 'jmin_polewear_official', 'joanna_jungeun', 'i_ove_mee', 'ddxhx.e_', 'ddoning_g', 'chic_crystal_chic', 'beast_best_park', 'bambi.yangyang', '_moon.luna__', '_jenny_sun', '_jjjjji_01.01', '_hee.ji', '9seor', 'jina_pilates', 'zzaeney', '0329.16.30', 'jiny_jico', 'do_y_blossom', 'navely_fit', 'diett_minnn', 'zio_o_zio', 'yoojju__321', 'yogii_bada', 'yeppi_0204', 'we_are_the_im', 'udt_physique', 'tristeza_duelo', 'thor__daddy', 'tab_whale', 'supermaster_photo', 'sol_daily_life', 'realbuilder_yangjaewon', 're_soup_wooju', 'purin__s2', 'oco.log', 'new_rora', 'nainkim', 'mongsilll__2', 'maingateisme', 'loveyyeonnie', 'kwonmira_kelley', 'kmcj_pilatesurf', 'kkangji_94', 'kimmirimiri', 'k.yewony', 'joom_i', 'jalabbak', 'hyohyow', 'hongringpower', 'hana_fit80', 'habbie_pink', 'felixx_lim', 'dearlove_____joo', 'crush_on_yuyu', 'busansurfergirl', 'bonita__chuu', 'boramkang___', 'areum_dapda', 'ang__zzu', '_y__ella', '__soul_j__', '2.joo_0', 'ssunny_7777', 'jylee_11', 'zon_machogym', 'zearnto_', 'zexy_bodyfit', 'yongwon5677', 'yeon_jewelry_', 'y.jjiny', 'y._.dahee', 'urimong_', 'spoany_rina', 'soo_hyunnnnnnn', 'seol_926', 'senxi_style', 'saem2__2', 'pilalimi', 'parkbyulth', 'nl_yoon', 'mzizzzzz', 'myposing_a.mi', 'my_yoon__s2', 'muscle.queens', 'mirrr_hera', 'miyeon3800', 'mello_ketch_s2', 'lovelyn__j', 'lady_body9', 'koo_je', 'kang_min__juu', 'k_0ju', 'ju_vvely', 'jjjinhyo', 'jiny_hong', 'j1.soo', 'h.jeong_diet', 'girlcrush_insta', 'geumabaeg', 'fitness_jinwon', 'fang.dana', 'eunminn_n', 'eeeun_kyung', 'bora.bitum', 'binmom__vv', 'bbangshuttle_v', 'bakko', 'arespt_sunny', '_ssong_411', '_h.ee_', '1amtangerine', '174_bana._.una', '0llllll0ii', 'yumizirong', 'mustfit_r_i_n_00', 'dahye7523', 'jxill.lll', 'eeechaewon', 'hazzi._.mozzi', 'voos._.soov', 'xyesini', 'pm_705', 'm11a._.404', 'luv.a_928', 'sso.ceo', 'yipinetree', 's.o_oah', '_yeeeeun2', 'zxcvchu', 'i.am_minji', 'hcompany_sh', 'soonzziii', 'yiara.kr', '164nk', 'sedyomi', 'yujn2', 's00bnii', 'tmdgp_e', 'muse__u_u', 'zzzl_030', 'kdheeee_', 'lanibiki', 'ssun.mimi', 'k_yomi_m', '_viiiiix', 'uniiioh', 'sans_ombre_', 'wandu.__', 'min.hi._', 'j.__.y99', 'hye.j1n', 'areum__132', 'minvly_1004', 'to.hee', 'ziiioiii', 's_kelly62', 'hs80o_4', 'eon_dony', 'ahhhhrom', 'hhh_aurora', 'c.hae_c.hae', '_001112', 'ete.angelbambi', 'da_hee.e', 'leesu_sua', '__5nyou', 'norinori_shin', 'ban_dalgom', 'yuniq.model', 'https.eungha', 'mal_lizy_ma', 'mal_ibbu', 'shannyy____', 'hyeni_fit', 'livvysso', 'bin_z___', 'gpals001', '2._o___.inch', 'jinyeong2_', 'somue_0', 'kt._.lala', 'hseee_miii', 'hawon._.k', 'sudingzelly', 'yumiadorable', 'anujinnd', 'sso0ii', 'kklbo', 'vella0327', 'daejeon__badbitch', 'pkciel', 'europe_now_jh', 'younjoolee_', 'su_zzi_09', 'we_are_good_company', 'y_yxrang', 'coo._.star', '_jrrrae', 'circle0_0wony', 'ooji__world', 'yeji_paof_', 'sierralavla', 'heekim_96', 'ssooohyuni', '3.26_es', 'apply._', 'aaaa_rumi', 'ssum1113', 'ondal__camping', 'leexzimin', 'bestlouishamilton_hotel', 'bob_oo_oo', 'yella_b38', 'adoryeong', 'sue__0914', 'aa.jjang', 'judy_diah', 'gaao_o', '__cherry_.pick', 'maison_de__bin', 'kimgaeuuun', 'july9day', 'pr.__l', 'j_sua12', 'jenny_lovelov', 'hyosiigner', 'ny_day_', 'yoo_deeng', 'walkadak_mami', 'dalmin_v', 'pila_dew', 'heaven_ings', 'wxxn_h', 'travel.s2_jjju', 'zamilakilla', 'jiyaco', 'konni_i_am', 'lovbbini', 'hayong_jjjj', 'zee.ni', 'yom__e2', 'a_y2e', 'jung_haejin', 'gonegwon', 'san_y0ung', 'dancer_feel', '_im_j._', 'guleum.bodyfit', 'sojoomi', 'how.haji', 'b_ari310', 'happi_zzubbu', 'floweryrora', 'helena_pilates_cheolsan', 'lovegxhxx', 's_sports_lover', 'shin1jae', 'jovely_24', 'iiyouzn', 'contact_beauty_', 'aura.on', 'realllllokxuxu', 'amyyyni', 'suha_1019_', 'mingji_156', 'ddubeeddubap', 'byeolnaerin_brow', 'love_me_vely', 'victoria__jeon', 'she_is_jian', 'fit_me_mi', 'jju_dailygram', 'buildingbigsister', 'hj.___.k', 'mi.ju_n.ng', 'j__o.o_', 'k.river.j', 'luna.__.s2', 'cherry._.muuu', 'hee.__.story', 'jkuss.swim', '_swimming_g', 'abiteatthecherryrin', 'minizero_030', '_hee_gyung', '_cherryjoo', 'yyr__n', 'may.s2s2', 'theperfume.avenue.kr', 'easyfreediving', 'roseedoit', 'aimeee.kr', 'alcedo515', 'sooolog_', '_ran_ju', 's2_unnny__', 's___juyun', 'dara_spo', 'lyndokk', 'hyuni__kkang', 'z1.an', 'dmswldlstmxkzz', 'seolahchloe']
    user_infos_list =user_infos_list
    ##2. 유저 분할
    user_infos_list = user_infos_list
    total_user_infos_group = divide_user_infos_list(user_infos_list, group_size=1)
    print(len(total_user_infos_group))

    ##3. db 발송
    send_total_message(total_user_infos_group, text, project_name=project, proxy=proxy)
