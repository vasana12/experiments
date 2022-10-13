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
    project = "hclass_woman_3"

    ##파일이름
    filename = "hclass_woman_3"
    project_start_date = "2022-10-13"

    text = get_dm_source.get_source_message(f"{project}.txt")
    # user_infos_list = user_split("""""")
    # print(user_infos_list)
    # input()
    user_infos_list = ['bodyus_seok', '_bin_stargram', 'queen_anna20', 'zumba__lany', 'ga_eul_pt', 'yun_huively', 'yeon_su_love', 'phantomgym_official', 'tg_swoo', 'allpeople_p.j.h', 'daehxxn__', 'hotplacegym11', 'tp_dhk_92', '2mippeum', 'trainer_arnolgu_', 'fit_h_y_94', 'jojun__0', 's2__u__', 'i.m_sem', 'best_kyung_', 'neiel_official', '158.ex_diary', 'yebin198', '_ya._.s2_', 'jumping_seosan', '16o_57', 'narea_vv', 'oreun_n', 'jjung_hee98', 'burpee_syndrome', 'dae_01_15', 'my_suya', 'myungzzoo_lee', 'cherishedjini.ver2', 'douce.hyun_', 'summer_nhj', 'damsongyorihada', 'tonystark0221', '_ha_hyeon_', 'whisen112', 'beast_best_park', 'jung__dw', 'hotplacegym10', 'skdlslw', '__03.12.01', 'w_dong_', 'asfit_gayoung', 'hjcsportskorea', 'eun_ji_daaa', 'xoxogunxo', 'ichbin_rach', 'physical_job', 'serif_j', 'ef.pilates_', 'guy_ms_', 'seul_in_record', 'wonhee_hong', 'yoga__hanna', 'by_glam1', 'go_mollygo', 'joy__.jpg', 'santa___jvely__', 'jiu_fitter', 'jiny_jico', 'lsangeuni', 'o.ne_fit', 'power_pd', 'an_na__u', 'cye_jin', 'hyesoo_1', 'cookuza', 'yamchae__', 'boxing_moo', 'hawa2ii', 'kkm_hq_gangnam', 'note_oder', 'mr.cha_ys', 'snu_judo', 'riwon___9204', '18.jsy_05', 'hena_hyein', 'violet.jung', 'ha_vely____', 'victoria_fitstory', 'hhhyunn_11', 'yoon.d_', 'victoria_ej61', 'on__simm', 'yeoshin_0415', 'ys__lee04', 'seung.il_', 'saoiilz', '1004gony', 'luminous__ys', 'eun_yy_02', 'sssujee', 'elu_baby', 'hey.o_o', 'favor_pure', 's_moon11_', '_yeo_ning_', '01__l2', 'holasu_', 'vivi_8685', 'jinxxbro', 'ohminho_1027', '______hm.k', 'roiju_kr', 'zal.fitlife', 'yoonha__official', '_yeon__jj', 'jaey__eon', 'y_na_2020', '98.03_27', 'ha._.binii', 'ssim_eunue', 'kkkjmkkk', 'leeeeminkyoung', 'workout_hyerim', 'mj0712_kim', 'yeo4_king', 'luiilu2_', 'woori_k_91', 's.mirae', '__delay_k_', 'hong_.11', 'zzap_tang', 'dk_ide', '3years_96', 'dear_dain0109', 'nina.chong', '7star.dia', 'pharmacistella', '9mi.0ju', 'eunstar1101', 'u_jiaterdot', 'm.j_kim74', 'b.h_u17', 'araariyo', 'sss.enter', 'cmy_ceo', 'skh2_2', 'bella_carmi', 'onethingaday_', 'lihavell_pole', 's._yeoniiiii', 'youn_pilates', 'jewdri', 'muscle._.moo', 'mimi.ing', 'yoonayang', 'la__bee_ni_', 'wrestler__k', 'sooyeon21004', 'della_linda_7', 'from_holy', 'munseok185.0', 'damheeee_', 'bluelemon204', '85parkjang', 'trehny', 'gim.6744', '0812_ssj', 'poohdory1', 'over.ring', 'ggu_1112', 'instyle_hee', 'hyennie_._', 'bbybyoun', '2.4_ljm', '170__jo', 'wc__js', 'raniet_94', 'april_jang_julie', 'mmmming_a', 'xh__jungx', 'songfit__sy', 'hi_zzeng2', 'honey__ddanzi', 'm2n_so', 'yubin__kang', 'hyunbeeny', '45__fit', 'tennis_ardor', 'what_a_shot_gi_joon', 'lullului', 'yu_jin._.tennis', 'ej.tennis', 'peace_kxx', 'draw.ham', 'u_ringding', 'tenn_is_o.o', 'tennisclaraa', 'zzzini28', 'proteinu', '_ming_min', '_ming_o0o', 'soya___pro', 'jw_lppeu', 'hairgung_ja', 'jaycho89', '88._______.88', 'shee_cheol', 'simeunae_zumba', 'jeonhyojeong5', 'may_9_melody', 'choc.o____', 'dbsdk0703', 'pitch.and.run', 'h_dare_u', 'azure_park_01', 'dear.seol_', 'elinbii__', 'limyoujiny', 'jooooo___w', 'han.sooah', 'minji2ppu', 'bslabel__official', 'gaheon___', 'yeowoo_b', 'young_ss8660', 'nabi.nalssini', 'its_neulbo_time', 'siaka3_3', 'limsseyo', 'hyeong__________', 'withbee_official', 'e.jayleen_', 'jjin2stagram', 'coucou.fit', 'euneun_uu_', 'oookkk33', 'bae_r_r_r', 'yooa.y', 'llllose_sy', 'euijooss', 'seu_oen', 'a.peachu_', '___.zia', 'allie_0227', 'mown_tour', 'haho_haaahooo_o', 'k.ju__h', 'hye_leeme', 'sk___seo', 'muscle_sudong', '___ze.ze', 'its_gym_soyoon', 'ridingaga', 'su_jung87', 'jisoo.x.x', 'jeje.newproject', 'm_n_u__3', 'bodyfit_yul', 'yang_songhee_', 'kang_16.04.12', 'lovely_jjinju', 'best_choi_', 'mi.log_', 'yoon2o', 'answer_fitness', 'eunnnnn0814', 'eunbox', 'julie9065', 'eunii_.157', 'youm1030', '2sunbro', 'red_daisy__', '2heeyagram', 'happysijoo', 'dam__diary__', 'strongzero_kr', 'metree_mall', 'pol.glory_01', 'ji__o619', 'cherry__hong__', 'jiyoung.lee100', 'miyongsik', '_yena_kim', 'mnfitness_official', 'love0825ff', 'juubbly', 'suk__jae', 'woojeong_z', 'ydg__0304', 'yanggeunhee', 'firstbody_gym_pilates', 'bae._.derella', 'feel_geun', 'ssunny_7777', 'dani.__.dani_', 'one_dietday', 'ssoramz', 'llynnnn__', 'roni_table', 'ohkyusun', 'p____byul', 'sooinkiki', 'jina_pilates', 'super_mins9', 'yuldong_s', 'health_rim', 'i_inxxi', 'hongstar2016', 'hssm011', 'habini_aa', 'mo_on.zero', 'namjun_kkk', '185_j', 'urban_jiujitsu', 'da_younggg', 'hipple_ze', '_k__sb__._', 'hye_ppeum_', 'n.aelii', 'yoon_move_', 'taeho_ham_', 'jiah_0527', 'srmozziroll', 'alphapurple', 'h__booty__s', 'yeunjji', 'psh__9', 'fit___hyeon', 'moonjh_ch', '2ogram', 'dietstine', 'ssssujin__', 'jun.2275', 'moonhyuk_jang', 'jeonhyemi0621_ifbbpro', 'dayy.gram', 'mongsta88', '__a_yeon', 'healthy._.chuthy', 'whitescus__', '0nly___won', 'woo._.vely', 'heiilin._.up', 'jeju_yun_yang', 'luv.joi_', 'kkk.yj___', 'h._.raning', 'jemissong', 'mialove1004', 'dlffjtm', '_ckjin', 'a_ssonghee', 'llool0looll', '5yeonsu', 'ssangb4840', '_mangnani_', '_ej_kang_', 'hexercise_14', 'zzzung__2', 'kunny_k', 'name_daily', 'maison.de._.eunjoy', 'zero_ssunny', 'kayoung_koo', 'h__nm_n', 'yw.tr', 'kwakjieun2422', 'sunny.gibbab', 'hulijia0206', 'merci.you', 'hyeogihyeon', 'attractive_031', '0315__js', 'juuu_0104', 'rachel_ty0', 'hana01071228', '__yh424', 'roooooocs', 'pinnnymph', 'sun99_moon99', 'mijin_aa_', 'parisjung', 'moogstar__', 'builder__lee', 'modernroom_yuyu', 'yuhyel_', 'joyful_127', 'image__90', 'hoon_1814', 'g________day', 'rubang_myeonjak_inhye', 'sunghee_44', 'seojuyoung1128', 'queenmun', 'jcm931213', 'castle_sm', 'jjeongsmom', 'sensitivity_hyun', 'hy_golflove', 'ria93lee', 'jae_hee__91', 'kang_body_', 'yoonyul_07', 'weonyun_27', 'you_easy', 'jinikwon_jeju', 'vdongmin', 'lulu__gayoung', 'hyen___k_', 'kyoungmi_choi', 'yoojeong0128', 'flutterer_camper', 'xognsl0120', 'kobongcat', 'seogangs', 'han_yujin_78', 'ssandy1983', 'hong.ssseung', 'master_trainer_b.a', 'lucy._.1229', 'leekoeun2016', 'soobean_o', 'sm_tiger', 'hwizin', 'shinaebabee', 'semvely__fit', 'jungbona', 'hj.k_pole', 'scelidopilates_jongam', 'joonsun_fit', 'heojae_', 's.___wc', 'jason_fit5gym', 'justdoitvanessa', 'j._.young_e', 'hyuni_fit', 'hyogym7_rosa', 'hyelthy_dh', 'hongra3075', 'olivia___choi', 'healthyyon925', 'healthy_jji_land', 'h_yojinee', 'minii___ly', 'luvin_victoria', 'dahwi_eli', 'e.j_choi', 'colorpole.d', 'k__ot.natural', 'cho.zz104', 'diet_kdy', 'jjoo_1115', 'cacheru11', 'bodycaregym_', 'jheal_official', 'jangddaeng._.e', 'bella_cherry06', 'j.eun_pole', 'cha._.y_lim', 'its_gym_hyeon']
    user_infos_list =user_infos_list[300:]
    ##2. 유저 분할
    total_user_infos_group = divide_user_infos_list(user_infos_list, group_size=1)
    print(len(total_user_infos_group))

    ##3. db 발송
    send_total_message(total_user_infos_group, text, project_name=project, proxy=proxy)
