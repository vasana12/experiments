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

host, port, proxy_username, proxy_password = "mobile.ipb.cloud", "7777", "customer-fydh21628401-asn-20057-sessid-RcPU-sesstime-1", "awR4Sad2t"
# host, port, proxy_username, proxy_password = "resi3.ipb.cloud", "9000", "MrIlCvzYImHc0I3t", "wifi;us;;;;"
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
        time.sleep(10)
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
    project_start_date = "2022-10-18"

    text = get_dm_source.get_source_message(f"{project}.txt")
    user_infos_list = user_split("""""")
    print(user_infos_list)
    user_infos_list = ['amy.studying', 'kimang0_', '_sy167_xx', 'qusckdtjq', '1_beauty_lemon', 'jjeon1133', 'hand_ull2', 'yunseonmi98', 'jaef_english', 'yoon_202009', 'min_s__95', 'wha_tthell', 'isidore.____', 'tompark0454', 'shingu_airline_service', 'the_people_invest', 'h__ui0_', 'silver_b._.7', 'jin_ah00', 'seong_h55', 'gaxni__', 'qkrdnjsal', 'gyeongirowoon', 'ooxoo.m', 'fly_byanna', 'minimi_land', 'daria___dfti', 'lucete.ji', 'flightattendantlifeworld', 'ktsh_official', 'silver._.west.j', 'k.eunsun__', 'ddori_glass', 'jjkdndjdi', 'abc_dxbi', 'jinniyam', 'dae__bbi', 'janelee.diary', 'ggab0108_615', 'j_yeo325', 'blessing._.y', 'homelandly', 'your__0', 'gu.ho_jone', 'awhite_spinel', 'fly.nana.jjang', 'sunhiydj939958', 'emanbo91', '_your.lily', 'dear.my_bestie', 'xinxxixo', 'davely__o', '_queexenn', 'crewfactory_jiyeon', 'fyzhyunj_90', 'brow_sic', '__kikuchan.j.__', 'ashywoom', 'ttie987', 'aki.nakatake', '1qaz0plmi', 'abc_hanbit', 'seulgi.nam', '910213g', 'lapunzel______', '6om1park', 's__elenee', 'yjulie_k', 'y_osc._', 'yonsei_7', 'flying_suu', 'ync_tour_m', 'wxo_oxc', 'yeooo_jin', 'modnishop_', 'wonder.im', 'vava.viz_128', 'want.house', 'az_juwon', 'twayair_cabin_tfunny', 'txx.il', 'theclassycloud', 'joongster', 'sukie95', 'sunjung__o_o7', 'spungy25', 'eunvely_00', 'seovly', 'sjufll', 'on___fly', 'jae___oo', 'nil_tnim', 'shopairbusan', 'miumiulai_1010', 's0__2mi', 'mallaeng_ee', 'saaa_jinnn', 'lhj3127', 'flyingpompkin', 'korea_silverbell', 'ra_around', 'kmsspeech', 'ecllairer', 'kd._.yoon', 'ps0h56xx', 'jjnicir', 'dozhk_v', 'jb_world.00', 'nayoungsung', 'awesome.claire', 'itz_tammyb', 'myportfolio_h', 'hyesug9_m', '1014ksw', 'hye0nse01_', 'monstercrew_narim', 'hg2077', 'dohicn', 'gonem9e', 'makecchappy', 'gimgaeddong365', 'z_vvony_', 'flight_yejin', 'm.seojin429', 'dreamflight_rachel', 's._.g627', 'daldanii_cru', 'joojiyaaa__', 'cozygirl___', 'sy__n_n', 'brigitho', 'jiinah__', 'beauty___o9', 'dmstj_0418', 'ariel_chaewon', 'i_justwannabe_me_', 'anc_kelly', 'ssensitivity_', 'airbusan', 'hw02_16', '_m_jayden', 'zii.m_', '2__sign', 'hoshipupupu', '184.2mm', 'of.bll_n', '0oez_x', 'foru.u_', 'ahreum_02.24', 'forflight_', 'abcdefg1234123432', 'dkfsip1', 'yeontirii', 'jacob_0623', 'wow91910', 'chhy1115', 'wlstns5284', 'play_636', 'winnercrew_official', 'bohyerella', 'vvwkka002', 'gabiniya________', 'vvinseeeeen', 'ayamyame', 'u_true_', 'ddae_un_222', 'ty._.kk', '_bo0_98', 'thugepi', 'aviation_es23', 'sxxyxunx2', '__gotsla', 'sul22222_n93', 'homehomehome0056', 'ssmall__world', '48._.3', 'soo.a.zure_', '__tnwjd__', 'smymy_0912', '1014_luvcrystal', 'selene_lee', 'crewfactory_jihyun', 'rladudxx', 'yooniyoon', 'riconil2', 'xxeoyun_', 'qrt8837', 'whatu_doo', 'park_yejoon', 'onecrew___', 'ouuuu0307', 'u_____m_', 'notenoughrunway', 'valentiney', 'neuroo.365', 'teddy_haram', 'n_y_cjj', 'chojae___', 'moai_smp_brow', 'ssujeongee', 'minayoung.34', 'toyottoto_', 'mia.y.moon', 'songgxh', 'lulu.studyeng', 'znee.__', 'kxsxymntlmdlmkdl463086', 'silverluvv__', 'ksb_1101', 'shit__the__f_u_c_x', 'jyo_drawing', 'seovvly_0_2', 'jujiyeon8', 'chae.lin_3', 'jo__melon', 'rucielmall__0002', 'ji_03.14', 'na_yeon43', 'j.crewbrow', 'rucielmall_0007', 'iam_soojin.k', 'naa_rye0ng3', 'i.am.zzang_', 'parkhu._.isacat', 'hyeming.__._', 'k_sirose622', 'hwani.94', 'oekaki202019', 'grace_._yunvely', 'babyarany', 'gggggnii', 'natural_lobster', 'flyerlinlin', 'jihyethejeong', 'evieweic', 'modni__shop', 'englisheveryday_withrose', '3rdb_profile', 'dj__pray', 'may_lily__flowerstudio', 'dk_arori', 'hwajin_nhc', 'dan.___.bee', 'kkkkisb', 'da._.hyex', 'arami_o3o', 'crew_wisdom', 'jew_jew_x', 'chentinida', 'eunn._.jii', 'centreeee', 'han_a126.0', 'brother_ho_97', 'minxeo._', 'argodrgo', 'g_4h__', 'abc_yeonyi', 'd._.yomii', 'esperl_mall1616', 'adauhrable', 'a_young0506', '_moms_crochet_', 'aahiine', 'chae_ko_', 'esperlmall8', '_k._.h93', '_ddaaain', 'esperl_mall1313', '_damddo_', '__juuuuuna', 'ch_ean_', 'effieeeenam', '______jy__', '1.hana_223', 'do__hyeong', '0ki_0113.m0', 'yeon2su', 'mijungpark_', '_yj.s2', '_sihyeooooon', 'daon2e_98', '0_0eeuu', 'da_hyun_o3o', 'yunii__j', '_damyee', 'd____y2', 'yuka_lpis_golf', 'yshan0000', 'crew_ridingjj', 'yh__loves', 'yeriel_brow', '_unring', '1.97_k', 'chaevely_s2', 'yeoinwoo_', 'yenee_english', 'anc_jh', 'yeeeeaz', 'ye.seo2', '03_hyunji_03', 'abc_eunhui', 'y__ttoning', 's.miyu0810', 'yorocorom_wh', 'pt_sia2100', 'pilot.gabe', 'pilot_eurotian', 'wo_ozn', 'oio._.cc', '_doli0ny', 'niho9544', 'sss0ni_y15', 'miss_royalkorea', 'oh6beeee', 'mings3381', 'soieemade_', 'min__k__yu', 'loisir_nxx', 'lumos_.j', 'rlatjdals_24', 'line_0_0', 'kang_sh57', 'leedduyon', 'rekn0t', 'kw_airline_service', '2jy_love', 'kjh45947', 'psychosis_hin', 'kimpo_cjfeh', 'k.mj17', 'jungwon_airline', 'neorok_', 'jinjin2045', 'x.xaspyn', 'iyoujeong862', 'midnightblau', 'incheon_jplus', 'genkiofficial', 'hello_crew_', 'mi__750', 'heujin_04', '1ujxn_', 'hanezine', 'letsfly_girls', 'ha0.jenny', 'cherry_.k02', 'h.blim', 'l_eunnii', 'gomaajarashi', 'lilyre_u', 'gochina_go', 'killer_party_hoseo', 'gee_one1', '_yjiiiyn_', 'fromdesign_studio', 'jjawoonyy', 'flying_maximum', '11_15xx', 'ethan_toeic', 'ixhyi_21', 'eat.fomi', 'yyugomi', 'dreamflight_berry', 'goldlinecake', 'donghyeongn_02', 'elenajeong_', 'dlog2206', 'florescencejh', 'dawonlk87', 'w00simvely', 'crewfactory_myung', 'dorywndus', 'choco_chacha486', 'rich.man_00', 'bufs_airline', 'crew_hera', 'bestclass_hyeji', 'tae__g0', 'bau_airline', 'by_hee2', 'aya_international', 'l_f.mj', 'apr__o', '_b.bo__', 'adeline_class_practice', 'sunset._.s00', '_gahiiiii', '_.focus_on_me', '__jee._js', 'jiu_02k', 'zzung_hy01', 'ww123ww123ww123ww123', 'msg_yo_', 'yuhan_airmanagement', 'y.__mom', 'younjeong2219', 'wisealex_', 'yoo_eunjin47', 'who_am_l24', 'wings_skycrew', 'kxpxi_s2', 'trhnbbuyer', 'valluer_', 'ssamourss', 'hmj_p_dh__', 'sh_magic_entertainment', 'sy_sept.29', 's.umsum', 'ham.myung.hee', 'robynne_kim', 'ssxrin', 'rin.e_xx', 'jxxhyn._.52', 'rani_emirates', 'rossanafriedberg', 'prod_redish', 'chlo_chlo_hee', 'pakaaaaaa__', 'q_yeon._', 'my___turningpoint', '03_hyeonju', 'mfyumuyrttgesfgbdfgns', 'mxxkyn', 'lkhoon83', '_nangni', 'lasoussus', 'ming_mine__', 'kyeungjun', 'jiwoo_flt', 'kiketrenes', 'michaela_0301', 'jumpsky8575', '2o0j0o2', 'jplus_suyeon', 'm._.mlsrl', 'im.govely_', 'tlqkfanjqhk_04', 'iam_joo.x', 'lnto.hs__', 'hun._.2e2e', '00.0218_', 'hong_skipper_321', 'jusparfums_kr', 'himama_1', 'jplus_eunzi', 'hello.leeyuan', 'jollyjjoo', 'hellocrew_sj', 'wooooo._.03', 'hanastudio_official', 'hyoiting', 'ggayeony', 'redfox219', 'flyingnekko', 'h_so_00', 'fire_sunnia', 's2s2_hans2', 'eunbimam4610', 'flybobos_747', 'edu.story12', 'valexu_', 'dream_on_air', 'dain_lovesyou', 'demian.__', 'lximjione', 'choijuil_', 'cerll_cerlll_enulee_con', 'c_nine__99', 'studiopicshere', 'beforedent_kr', 'bodywellfit_kkj1028', '_1992ing', 'liz21_kim_english', '_hyorini', 'xianling43', 'beaut.__yy', 'comme_jenna', 'jjiiyoung_k', 'w_b_yeats00', 'lxxdonz_', '_jeong_w.02', 'yxxsxl', '_eupho_oria', 'vkim_ehlschlaeger', 'vh_academy_', '_aeonian.k', 'toua_univ', 'the_satti']
    ##2. 유저 분할
    total_user_infos_group = divide_user_infos_list(user_infos_list, group_size=1)
    print(len(total_user_infos_group))

    ##3. db 발송
    send_total_message(total_user_infos_group, text, project_name=project, proxy=proxy)
