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
        # time.sleep(20)
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
    user_infos_list = ['sanszerodegrees', '5627_yun', 'yeon_piece', 'viktoriiadorofeeva9490', 'omeonepsycist', 'y_sneakers.official', 'shy_for_love', 'nunique20', 'min_sun_03', 'lwmuaqw719585', 'ulha410', 'marksaku.james', 'lissom_store2', 'jootwentyfifth', 'minzonga', 'ewest_j.14', 'dreamcometruewith', '__suxm', 'daily.bini', 'su._.star.03', 'rlaeogod', 'im_joori', 'bei_delli', '_kyunnng_', 'toshhikoo', 'ye_nye', 'seo.j__in', 'gold2oak2', 'goddohoon', 'kwonminsung_', 'rinirinrinn', 'sleepy_ash_00', 'komie_the_cutie', 'nan_yeahbbunee_', 'hicutie_official', 'gsfwer234sdrfee7', 'yu_m_iie', 'bo._.bble', 'kimhoisalon', 'marlenicm_123', 'bbanggujiwon', 'sojin.__.__', 'ecmother67', 'charl_bit', 'sh54s578y45sj42', 'banibanisense', 'hajunn_mom', '0_ciliegina_0', '0_00_0.0_0', 'sk_gongju', 'ddang._.ee', 'fdsfwer234sdfer', 'sweet__bbo', 'eal_fashion', 'light_rrri', 'j_nadya_hope', 'dnuh_mngi_', 'ekpinqyzy', 'yejoqt', 'delectable_taste_', 'kensington_yoido', 'twinkle_hari', 'yeoyura__yul', '_a.victorovnaa__', 'cute_gooreum', 'eungssoooo__', 'super_chch', 'cbvcbfg1523', 'insta.katepark', 'sunday.08', '__merry_go_round__', 'kosa7853', 'w.__________.a', '_dlehdgk', 'qweas123452', '______liujinxi______', '0ru__ru0', 'lee_wngml', 'suntdnt', 'youn_deuk', 'liz.jeongin', 'glen_park', 'casa_rim', 'banri.official', 'yu._.your', 'tho_onna_unny', 'anloislovesarts22', 'nyangi._.i', 'toponslr', 'gaeul_ella', 'canvas_graphy', 's__zzi2', 'lissom_store1', 'yoon.woo.joo', 'only3you3', 'cutie_2jun', 'hyo._zzin', 'ahyoon0914', 'deokgootagram', 'sehee._.vely', 'ra_joy_67', 'lusty___official', 'smile_photo_1', 'incellderm_suji_with_miracle', 'jwjqkghhasuu', 'kkong_.min', 'glmr.klls', 'hee._.joo6', 'iseolida', 'sinjihoon24', 'inqlsdl', 'hyein2_', 'discovery4plus', 'beautiful_mom_acc', 'biki_beach', 'festive_daye', 'star_young.eun2', 'yeon_2_c', 'jeong_h_y2', 'dust98', 'mimjmimj', 'biki_rina', 'ingrrlaqls556', 'class_man33', 'il_ddi_', 'ryeong8928', 'hyeok.wn', 'aeter_0', 'lookbylookk', 'mpmeiners', 'charlesthesecond_', 'rodgersybz.paulette', 'fdsfgvdgvbf75', 'charles2_12', 'no.1_bkm', 'kh_jy10000', 'rmsthstlf3g', 'delgadovth.teresa', 'mikkypuple', 'moon82206411', 'i_m_yull', 'eonkyupd', 'couplecandyshop', 'brandmall_987', 'djz.489', '37th_look', 'n__limit', 'l._.an.k', 'lkjkjk8', 'dagyumwoo', 'yyssyyy_', 'yearning_47', 'today_clothes10', 'connerfwh.tami', 'simple_no_more', 'hbqcuzvonvfwhk369375', 'callmekellin', 'joowonlive', 'ayersjrl.ada', 'happy_in_ing', 'h.b.d_closet', 'amalis422', 'eoqkrskwk87', 'dwincessant', 'fsdfsdgwer2345', 'annyeong8407', 'due_baci', 'daminim._', 'y___0_0___n', 'asome_company', 'bluebeam._', 'hvk_louis', 'felicitayinren', 'unhyuk.yun', 'anarchia_daily', 'sexy_acequeen', 'seoulsanai', 'dlrhkdrl1026', 'seoyoon282', 'kimijjoo', 'paminestore', 'seokhu_0307', 'modernari__', 'love_deary_0527', 'carlos_shaforostov', 'dfdsfwerfer', 'rou.ca.92', 'hyoala_', 'hi_jooyeon', 'polra.riseu', 'dfhgfuity8', 'da__0i', 'clarisaharamara', 'park_bull', 'coco.melting', 'cocomelting2021', 'knowstock', 'cloj_official', 'fanspage_bustymodels', 'vinbro__select', '_silver_daughter', 'xrapachevawiktoriya', 'vanne.vi.co', 'bob_minjae', 'kimsoo01122', 'ably_ckakri', 'ddooory_14', 'zest_fashion_', 'ba_ra___ki', 'richardhartleyer', 'withmodern', 'omyssol', 'parisiangirl3110', 'nanaru7', 'm_morpg', 'ddo_0hyo', '163.86cm', 'lulu__9805', 'k_friendly_52', 'jnroh', 'kerrmve.irma', 'iminl.ve', 'hyun._.a_____', 'ai.tsubakihara', 'daynight8888', 'f_elice1', 'commonz_official', 'ashghaskdjkqwj', 'cobalttbloo_', 'mabuakershaheen', 'bfdra4gg75583', 'young._.bbi', '2seul_e', '_secondconcept', 'kmina_93a', 'gkwjdll____611', 'sumisuwan_closet', 'youn_aaa12', 'roselevel________', 'pwill_p', 'sooen8886', 'xzvcx434', 'xodrnzmzmzm', 'pick.j_', 'ootd_dinit', 'wnnnw1004', 'nara_0908', 'me.we.me', 'wilderfiv.maxine', 'whitecrow17', 'maisonde2', 'kmbiii.__.519', 'rosegirl_0430', 'jaily_jaily', 'hy0_07gk', 'irene0211t', 'kahyeon0905', 'sang__core', 'sdfwerwr234234d', 'lee_aaaaaaaa12', 'harinnn__x', 'han_nyang9311', 'kana__s2_', 'gujahye87', 'ednavigational', 'rehclaremont', 'jamongcc', 'avenue197_official', 'dmswl00111', '01haewon', 'bagseoa154', 'psychoplus.jj', 'd.roooom', 'ttje___', 'tastesharehaeyo', '_msune', 'say_seo_', 'ppeui_vv', 's_hj705', 'moodnmix', 'mjkim10587', '5nuldomari', 'may__french', 'kyb0227', 'lllbluell', 'nobbans8', 'wjdgus0011', 'leeinhye0603', 'iij_oow', 'hk_jh0606', 'yexxu', 'dear_timing', 'skjdwh__5e6f', 'branchworks7', 'yen2tattoo', 'da__in.s', '179.cheol', '_________txoxmxixe', 'heon.e_622', 'mariamls', 'scw_82', 'zlssun', 'jueun__0', 'im__joli', 'mcc__onni', 'ehyunfilm', 'rajimorara_00', 'rlashdnwns', 'havevenjoy', 'yelin_961', 'ka_na.f117', 'daehyuninside', '2_0x3.5_5', 'ye_ye_sa_ma', 'lookbook__a', 'kang__hojung', 'apleasurforyoureyes', 'karasuma_ayano', 'pink_peachshop', 'ye_song', 'y._.esfp', 'sziniz_', 'yoon._.vely2', 's_ojjjj', 'ilxxso', 'dambi_apple', 'guya.2019', 'h_juruju', 'cyon_03', 'ellvely_official', 'apnalchangchangkimhyungyeong', 'taek.taek.kwon', 'fsgdfgert345dgrt', 'tindaltamatha', '__pjy', 'yonn1n', 'squat.kwon', '171_uz', 'ryu_sds', 'magsoni_felicity', 'aelaelyu', 'lsk9_9s', 'lib_ra___', 'kim_s_ofo', 'siiis._look', 'j_u__na', 'iixin.zoo', 'hi_flower_ssong', 'fgdfgfd45569', 'siwoo_______0609', 'kim_dh.95.2', 'ggo_ma_mo', 'bin_08_31__', 'iii_17.0', '_luv__yeom_', '2_october_', 'wise_lover_0113', 'chajinah_', 'yeahsol', 'ssunjassi_', 'sss_bi.n', 'sssf._zw_', 's_unve1y_', 'dryjhg4654', 'ssbb_bba', 'parktttthhhh', 'one_j_water', 'karenchttt', 'yeon0104', 'windycity9200', 'w0nday_', 'hanarin.shop', 'yougolek', 'missadelineong', 'dday_happy_62', 'blackcheese_off', 'sdkgjgjjgja', 'inooyoes', 'david_sw_j.in', 'qaz12341999', 'eee.kyeong_', 'may__french01', 'ggeniie', 'sbs_abracadabra', '_espacio', 'js_harinis', 'zonyeokk', 'luluna_7821', 'ha2eul', 'eunding___', '_november_10', 'yujinx.__', 'cclida_aj', 'sweethebe_hades', 'kakui._.jin', 'tangle_mina', 'jjo_chh', 'insting11', 'ss_le18', 'hyewon_.k', 'min_y__777', 'jy_p09', 'i_am_a_cow_boy', 'huluobo77', 'h.yeon_o4o5', 'eung_hye_0416', 'bboing_luv', 'cuties.ennggu', 'closet_suyean', 'your__hyun', 'wjddms0142', 'y_hs_xx', '___onlygyu', 's_hee1999', 'gmsdn_151', 'mong_zzarella', 'godseonguk', 'fddfgds5465', '_sayonara_bae_', 'yyuni_96', 'dam_.som_.kong_', 'kxonoxin', 'zamboasa', 'jerry._.0805', '_jyenll', 'j__md_99', 'milk.honey.daisy', 'hxcorita', 'dj9743', 'jdng.ot', 'at_your_su___s2', 'minimichoi', '__jeongexn', 'generalist_one', 'eli_02002_i', 'winter__kid_', 'be_c.ca21', 'rally_live_', '5_gyeobsal', 'saintphotolife_official', 'yi._.iy_2', 'haebaraki_dream', 'yex_oeo', 'dmsal0421', '_moosoon_', 'ubirajarajeferson', 'morethan.lynn', 'saintphotolife', 'lovely.__.jung', 'gun._.dust', 'dearjeanne.shop', 'draw_park_', 'christine_6.12', 'woolimjune', '__da_on', 'cumpenvitalis', 's_hye_97', 'nado_girlfriend.look', 'mingming_221', 'nanoonyamadi', 'hjjim613', 's_e_y0070', 'ming__s__', 'daaaaa_codi', 'jyofree', 'ji_min_aa', 'daegu.coco', 'irondragon_cat', 'i_dont_listen_to_my_mom_', 'ralumu_00', 'colorebianca', 'hyegean', 'gonuyimo', 'choosinghmmm', 'fxxkkkkkklazy', 'deejaypeach', 'ackel.coelho', 'adaline.sin', 'deeeeeep.o', 'ddodin.kiki', 'blairhong_', 'averilholathana', '_imyour_lily_', 'blackk_mandu', 'binggu_x', 'bear__0902', 'luv_seuls2', '6crazy_baby9', 'solisrji.vickie', 'comley.hy', '08_sm528', 'v11.16v', 'whpoets', 'minjihyeonnn', 'min__dung_', 'xy_mong', 'photo.pandaemon', 'what_up_82', 'luv.ya_o', 'ji.m_in7', 'uni_fit96', 'iam_southamerica', 'hye_ys_', 'sang___mimi', 'sistershop505', 'hr__cc', 'rosie._.cc', 'h.yo_seon', 'pawlaksimone52', '08._.20', 'x_xuxin_x', 'aegimojji', 'p.crystal___', 'ze.lee09', 'manon_tattooer', 'oribeegle', 'teeny031113', 'olmayny6606', 'onl_ootd_', 'miasaka_kim', 'jjnnii_ii', 'lalamake_official', 'j__u__0927', 'juuuu__s2', 'p.ra_y', 'je_11.28', 'h_bin_19', 'ha_yuxxl', 'maimar_m', 'dutchsamo_bokhee', 'sdf_4881', '_honeyb2', 'iranshop.smartstore', 'luck.cbd', 'ziniziny_', 'co._.m.ely2', 'space_music_entertainment', 'park_ye_jin___', 'im_cat_candy', 'buddha2_1', 'hyun_9ook', 'dressingroombystar', '170.rring', 'gocha1zzz', 'jun_060925', 'winnerpeng', 'hesterdht.simone', 'heera._.dress', 'evil_ffyr_ffyr', 'seoyoon._.d', 'qerqwu', 'louiethecutiepie', 'elizzab.tta', 'gaeunlee__', 'dior.my.kitten', 'chohee__s', 'iloveonigiriyeah', 'disel_newell', 'ee_.room', '1song27', 'sz_pink', 'qt8garments', 'haji_hoon', 'ksenialaiblly', 'm.luv_ji', 'km.co.kr', 'lovely_ssongpr', 'hyemnida', 'digun_ko', 'guzmanftb.celina', '0lyuna', 'chae_n2_', 'snowwhite_hk', 'newyork_153_si', 'life_is_coooook', 'hye_o_o_dd', 'e.jiah._.bunny', 'gaenyi_243', 'blossomeun', 'xxoluvv__o', 'cristina_mulyen', 'diamay___', 'h__jin_sil', 'ladida_market', 'xx_bari_', 'hair_make_cachette', 'westc0w', 'ehgml_16', 'princess_young17', '_dasss.u_', 'jsoo._.eyo', 'yun_gyo31', 'cute_girl_member_', 'fgbhdsrjhg', '02_7_46', 'ssss_barbie', 'you__bitna', 'thenew.max', 'antje_schwed', 'babi_and_lady', 'yef_korea', 'pie_vv', 'hyevly__01', 'leemi_ni', 'gameunbin80', 'venus_jk1004', 'hi_soyee_7', 'shu_stagram00', 'l_ms_330', 'lovehicutie', 'a_one_dani', 'jeon_jiyoun', 'e.the.re.al', '4_26_ming', 'a53752159', 'wook_88_', 'seongbin_pang', 'dalcom.han.i', 'lets._.zzini', 'w0.oon', 'hye_ppppy', 'kimnamho92', 'daniel_diary.ykd', 'seonhyi685', 'sweeti_l9011', 'dasfda6', 'kimeunhye6689', 'hayunming_', 'avec_bora', 'preeety_puppy', '___kate_oraz___', 'yenaqt', '__fairy_yg_', 'strivewinme', '99_jaejae', 'jihye_86', 'melomantic_nail', 'cutieprettyangels', 'shuya.qiu.56', 'som.is.not.cotton', 'klerkerero', 'mi_00sook', 'jh_azure_', 'catrlaqls', 'yahil_toy', 'by_russianblue', 'teddy__woo', 'galzmao', 'qweas123451', 'oh_good_song', 'yasi_ya_si_', 'lovesome._.mk', 'oh.joy_', 'kjmreuta', 'tori_wang_ja805', 'haneunbi_', 'asdasdqwe123125', 'jaewoo_choii', 'j7295_188', 'qtqt78', 'bagsunyeong2366', 'i_lfsm_0', 'hk_kr_josh', 'szfcdxgfg', 'lee_dark.heni', 'nan_ii_93', 'hwanni00', 'lifebook.official', 'ilooli13565963', 'knj9154', 'jam_geun2', 'yamche11', 'hayo0915', 'shine.joshua.onnuri', 'yunhyeog793', 's2ong.4.me', 'kangssam2', 'aetude.dgraph', 'ha_yun_s2', 'shin_seohee', 'gilho0628', 'pdw1103', 'fresh_bean', 'ann_hae_zi', 'naastassiiss', 'yeahhapp_y', '0glo7n', 'havenochoicebut', 'ivorywhitebunny', 'oh_yeonah', 'wi_wi_wi__fanpage_', 'cutie_tina_me', 'jiseon_tv', 'choi__selfie', 'jaedoyu', 'gent1enatuured', 'velysoo23', 'soonsoo_siho', 'seokkwon2', 'jayee_1019', 'glamour___shot', 'k_hotgirl_com', '_arisugava_tae', 'gsfrete53455', 'sujinyang96', 'tambody_official', 'mk_muffin', 'ra_c_00', 'nnnnssjjjj']
    # user_infos_list = user_infos_list[100:]
    ##2. 유저 분할
    total_user_infos_group = divide_user_infos_list(user_infos_list, group_size=1)
    print(len(total_user_infos_group))

    ##3. db 발송
    send_total_message(total_user_infos_group, text, project_name=project, proxy=proxy)
