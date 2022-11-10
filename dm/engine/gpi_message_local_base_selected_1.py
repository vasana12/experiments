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
    project = "hclass"

    ##파일이름
    filename = "hclass"
    project_start_date = "2022-11-08"

    text = get_dm_source.get_source_message(f"{project}.txt")
    user_infos_list = user_split("""""")
    print(user_infos_list)

    user_infos_list = ['sjeuro', 'olivia.beauty.bar_', 'sota_collection_official', 'born_almighty', 'tiqcpfl1004', 'hyo_ve_ly', 'sage_aka_neul', 'mouvoir_7', 'alien_seor', 'ykk58230', 'sooimk', 'hyoju7438', 'ballerina_leh', 'thisisjioon', 'joongangilbo', 'clair_dance_studio', 'yj.poledancer', 'beddrawing', 'boyun_choi00', 'n._.eunchae', 'yeonju_pila', 'delay_golf_pila', 'heart._.bb', 'rosa_kim_', 'alumcho', 'honghye._.620', 'nam_keun_an', 'one2ya', 'sjassa2', 'soomilog', 'seah__yoon', 'it.herena', 'mmiinseo', 'wasdy_ceo', 'rhythm_angels', 'joeunna', 'dongha.ria_liebe.be', '_e.del', 'shine.sung.ah', 'gy._.1202', 'commando_play', 'y.s.eo', 'kkk.uuu96', 'hhj0714', '_belle_j', 'yunvely._', 'xolovekayeomi', 'rainyrrose__', 'mauve_beige', 'ksj_sketch_', 'hyun_yuha', 'fre_ezia', 'design_seolwon', 'ballet071029', '95._.bong', '1seob_', 'haeku_', 'jeong.__.98', 'daxvuiz', 'yyss___04', 'yu_j_2', 'ysomi____i', 'xul.eb', 'theminhair_sojin', 'teddyjllm_j', 'set.__gram', 'roniboutique__', 'lyxryu_sena', 'kimmanjiji', 'kim_ji_won_1114', 'joonhwan0l', 'eanhair__ahin', 'balletin_pilates', 'ballet_s_h', 'ballet_pasha', 'arco_reborn', 'achieve_diamond', '_jee.hae', '_dish.geom', '2l.u.r96', 'yoonah_with', 'y.o.u_sine', 'sempiter_aube', 'lys_10.17', 'kang.jh_dimom', 'ju._xy', 'jhousehair_junhwa', 'j_hairshop_', 'heart.gulum', 'bongsoong_i', '__beom2__', 'dalsia819', 'yeoung_seon', 'roadand_hyun', 'mosup_one', 'mojo.b.positive', 'mlnlog', 'mink_hst', 'ma__mood_', 'jjj1005', 'jbodystudio', 'hye_sumi11', 'gardening_diary', 'damda_flowercraft', 'choooon_', 'astrum_.flos', '_yeonglovesyou', '__hl.ync', '100.j_y', 'usalm0n', 'woozu_like', 'su.__.rxx', '203_ubin', 'vivieeeeeee_', 'u___ai', 'theminhair_eunjin', 'the_ballarepil_paju', 'sor.pe', 'soonsoo.ballet', 'shes_yoga', 's_yulvely', 'rozetta1017', 'royalsalon_donghwan', 'ranggu.ddo', 'paletteh_jireh', 'nafall2541', 'mosup_mini', 'm.02.923_hair', 'le_en_ballet', 'l_ye_won', 'jaei.susu', 'gounballetfit', 'easybusy_', 'doy_lemuse', 'dear.elodie', 'danafit_plus', 'boutique_hapjeong', 'bayby_rosy', 'baebaeun', 'ador_xble', '_hyn_princsss', '0vek_03', '50kg__girl', '____muggle__', 'sohi_yy', '_withballet_', 'zl.ynn', 'yul.__.vv', 'sunryuni_z', 'sssseo_01', 'ssalssal0324', 'rin__queen', 'ode_pneuma', 'naneun.____', 'na_ballet_', 'loveyjzz', 'love_happy_lucky_', 'jjeongstory_1', 'jeongpink.s2', 'in._.narnia', 'hyuneair', 'felicity__offical', 'dieterjeong', 'da.o_o', 'balletdebon', 'anna_pineapple99', '_luminous_jh', '3story_yoonha', 'minwoong1985', 'yun_yun_san', 'yj040422', 'y.ssora', 'wonneee_', 'vivid__h', 'suuuu_hayul', 'sukke_yun', 'steps_boss', 's.lluvvu', 'rosely_ballet_art', 'releve_gyeom', 'pppparkyoungen', 'min.o11_', 'lereve_balletwear', 'lbrown_ddohee', 'jinheekim_seoul', 'imjess_p', 'choi___rin', 'beeeachy_', 'b_so_y', 'ay_____0223', 'amor_balletpilates', 'aja_aja._', 'sejong_art_academy', 'ballenaflower', 'y._.seulkki', 'kh_ballet_academy', 'yeonjeong_hair_', 'ye__.rxixgu', 'xxyunaxx_lim', 'vvorasdesign', 'tomodamomoko', 'the_cclim.h0', 'shuballet', 'reumi_balletpila', 'rani_fallll', 'namaste_hyun', 'mybrew', 'min.seo_____', 'lasuit__official', 'kooolour', 'jyu_ve', 'jusilver._.k', 'jiny226', 'inlovelucky77', 'hwangga__', 'hi_luna_rom', 'gkwlangkwlan', 'gktmdtn99', 'ershyoshow', 'diosa_tangodress', 'dianaquezada', 'by_hamiyou', 'bdbdbd.b.d', 'ballet_some', 'aimstudio101', '2.21ml', 'yubin_873', 'hyeleechu', 'star.bean.hang', 'sol_hairroom', 'seojeong._02', 'ruverly_', 'jinhahwang', 'designstudio__j', 'design_works_make', 'choigaeul_sseol', 'bob_minjae', 'bll___lld', 'balletically_offical_', 'babih_ee', 'yyoonngg', 'yoo.vely_n_chat', 'seein_studio', 'nla_workout', 'na.movements', 'mosup_yk', 'joonhair', 'jinny__z', 'hannabodyfit', 'gratia_goodnews', 'formyangel_daily', 'fobene_sport', 'eun.seo.mom.1024', 'danbibic', 'chloesdh', 'cherish__per', '__yoooni_', '__k0608', '_.dvale', 'reum__st', 'ballet_arts_gunsan', '_ria_baby_s2', 'youngkk__7', 'youngs_sss', 'smk_dancewear', 'sihoo_latte', 'shine_lar', 'seochanglausanne', 's__heeeeee', 'royalsalon_seoyun', 'raina_0203', 'precious.like_it', 'myjiyi', 'miyahime', 'mingyu3190', 'lovely_ayoon', 'leegayoungs2', 'labelle_ballet', 'l__yj', 'l_pila_s2', 'khw_1335', 'k.mango_yul', 'jun_wardrobe_', 'hyejjin_ybb', 'grape_song_e', 'garma_harry', 'deuxiem_jeanne', 'chaeichloe', 'body_line_pilates', 'aile_ballet_academy', '_oh_always_', '11_yeseo.1026', 'yeni_stargram', 'duwjddlekd', 'thecozysalon_camp_humphreys', 'shballet_official', 'princessjs7', 'nuvida_caleb', 'leeseul0683', 'lee_el_love', 'jun2day', 'jjeonji3142', 'jinju3402', 'hs10_hj11', 'hokeep', 'fiore_bb', 'fancy_poyz', 'cs_yxxn', 'coiff1rst_jdw', 'bolpeede', 'bobbys_hair', 'beauteee_ury', 'ballerinass', 'asuka0119_official', 'arcovaleno_icn', '10brikjy18', 'jin785214', 'juni_mom84', 'balletomane_mokdong', 'zsh_yhz', 'ttbt_official', 'theurban_in', 'ssssky_ballet', 'sssssssu_hyun', 'soyul_0923', 'salon_blanc__soeun', 'rogeeaube', 'movedeforet', 'miingzyyy', 'lavu_n_j', 'jung.chaeyun', 'jjaeyoony', 'isports_zzanggu', 'hyu.rim', 'hanbitdubitsaebitnaebit', 'han_donkee', 'gyuhyun_hh', 'eru_pila', 'doyoni.94', 'bonita__e', 'azit_bob', 'ayangartscenter', 'annpilaballetfit', '1206_secretbase', 'byelin_jattic', 'l__j_ryun', 'hanh__hn', 'yugnng', 'yejin_jjang', 'suemeway', 'soo_rhythm', 'sinseonhwa__85', 'open_the_body', 'minhwee88', 'mimemamemo', 'miline_ballet', 'jini_studio', 'jesuisbamtolrina', 'hhypia', 'doa__anna', 'dadaflower__', 'blueworm5', 'b_b_studio_', 'adorable_nab', 'luv__arara', 'jjeong_ppeum', 'u.n.i_i', 'bb__min', 'gabi.iiiii', 'y.o.u_doha', 'toptoe.kr', 'sujin2650', 'starry_jannie_', 'sson0303', 'seulvinski', 'peniel_jahee', 'minyyomy', 'kange_89', 'jjuhee1214', 'jee__.94', 'indeep_second', 'iilove_sky', 'hkyung_snmdel', 'enciel_yina', 'cha.jui', 'bongja._.c', 'bomvelymom', 'bk_iloveyou', 'adorable.__.eun', '__yumble', '2019.10.01_ari', 'neuru_psk', 'lovely_yuna_gram', 'salondelumen__jieun', 'ella_fleuriste', 'unroom_soe', 'u.arc_chaea', 'simsballet', 'seon_a_j_97', 'pbet_studio_official', 'mo__on__light', 'mean__pic', 'lee_89.12.12', 'khyballetacademy', 'jjoony219', 'hi__ari__', 'haseebrosis', 'gomiso4970', 'gggga_yeong', 'bellus_pilates', 'ballet_epaulement', 'andonewools', 'americayoga_gy', '_memymj', '_hyun_e', '_formyangel', 'balletmimi0', 'ahrok_the_ballarepil', 'olor_yoga', 'mond_pilates', '36.scene', 'chawon_pilates_balletfit', 'wan_of_things', 'vinca_raon', 'tophaircolordesign', 'team___a.d.p', 's2eoyoon', 'rubina._.1002', 'royalsalon_k.uzin', 'mutnine_ra.l', 'muselight.official', 'marys_stretching', 'lovely.kje', 'libbkimpro', 'leeso.d', 'lami_gaeun', 'juliaballet_songpa', 'jeongara704', 'hyunwoong__kim', 'hee._yaaa', 'happysonny82', 'eir_fit2021', 'eileenlovesgucci', 'dowee_ssaem', 'dear._.stelletta', 'cleverclairee', 'chloe_myungju', 'bbangllet', 'bao_hair_taeri', 'adorable__j.h', '_vovrin_', '_mihae_me', '__jeongeunn__', '2.sovly', 'nu_ri_79', 'crystal.sj_', 'lovesome_ballet', 'eunchae_jihee', 'zs._.su', 'yun_d1001', 'yejongpointeballet', 'whitekome', 'w0nd2r_w0mxnjh8', 'velu_vel_y', 'u_nvely_', 'suzzzzyi', 'sudal_sudal_kim', 'soyoon.fit', 'soo__1120_', 'sooa_mam', 'smile_daye', 's.sheeeee_', 'mia1202v', 'lovvvelyn', 'lovely_plump_', 'jung.a_83', 'jiyoun_like', 'ji___iyoun0', 'jh.luv', 'jeongjini_', 'hotsuz', 'hanaiiv', 'haga._.fit', 'h__yuha', 'gmltn4r', 'g.r_lee', 'dongunniee', 'chopper_bareun', 'balance.84', 'bada_collins', 'all_about_jin', 'abalbae_wear', 'crazysonic08', 'eunjung_lee83', 'ballet_jieun', 'kkomseul_', 'tthangyo91', 'truth0119', 'theaterballet', 'saipan_life_gose_on', 'romfit_diet', 'purple_n_min', 'pf_mjcho', 'multi_player_mj', 'mamigood_life', 'lovely_girltwins', 'lee_hyunji', 'lareveballet', 'kookminpt', 'jiyoni___i', 'jinjin______e', 'intae_resting', 'i_move_pilates', 'hairbydaom_sara', 'flos_elin', 'euhyerim_', 'eclore.hair', 'dudu.dung__', 'dpgpfkeldj11', 'cute_soming', 'beau_mo_', 'amodomus', 'a_diary_suna', '_lovely_1044', '__morelove___', '8.29___', '1uv.mi', '0ju_0ju', 'choi_siyeonn', 'heungmommy', 'jubro11', 'yeon_seo2018', 'downyballetfit', 'cha.yeon.woo', 'zzuriya_', 'yulyul_bebe', 'youngjo.kwon', 'wba0617', 'vshilarion', 'stretching_and_you', 'ssemiz', 'siyi_angels', 'sheep.dahae', 'seol._.2_', 'saa_rang_', 'ran2203', 'rahel_ballet', 'rael_balletstudio', 'r_i_m_2', 'r__evoir', 'ppeu.mi_', 'pila_de_ballet', 'pastelblue7', 'park__ej09', 'ninam611', 'mylove831004', 'my._.harin', 'muse_yeouido', 'mohani0969', 'misook0319', 'luvharibo_', 'luvl_rami', 'lowe_fil', 'lovely_sosung_', 'love__kyul', 'lalitosoom_official', 'ksuggi99', 'kko6534', 'k.yy0619', 'jiballet_edu', 'jh_fitnessballet', 'jei_doa', 'jangseonhwaa', 'honeylintutu', 'hi_lyxryu', 'grace.eun_beauty', 'gamdongmom', 'eunbori_life', 'dream.hong', 'dewdim.park', 'da180818', 'chocolate_yoon', 'callia1212', 'boutique__yj', 'bonaofmay', 'balletmihak', 'arnault__16', '_chaevely_love', '______eunaaaa', '_____2_0_3_', '6nthespot_j', '00sinbee00', 'ji_hyun38', 'hyeri_0623', 'dalrangbom', 'siyeon_sihoo', 'chaebly_daddy', 'gyeoming_ballet', 'hanaya41', 'hari__lang2', 'milatutu_kr', 'yulrin_mommy', 'yo_na_ru_rin', 'yeon2__0', 'y.o.u.n.g.d.e.o.k', 'xoxo_jjbhn', 'uoo_bebe', 'uklovebo', 'thesom___', 'suny6253', 'sooamom._.eunmee', 'soda_emom', 'sh_kwon77', 'polerina__', 'nayoung_hi', 'my.jiyou', 'mmong_f', 'misskorea_song', 'minimistudio_', 'love_yj17', 'lalaballet17', 'la_vie_ballet', 'kimjeongeun5452', 'kim_sh0507', 'jin_jjjju', 'jihye__2002', 'i_am_minseo_', 'hwamiju_hyun_a', 'h_yooniiee', 'h.neul.j', 'ej.sunu', 'donnouncer', 'daaeun_i', 'coin_yum', 'cocory1030', 'chaenymama', 'blackqueen_seattle', 'barbiechloe77', 'bambimom_', 'ballet_thera', 'azureballet', '_dahyeon_mommy_', '_a_jung_a_', '__lovely_jojo', '935najuhee', '3eun_91', '2jy_____sy2', 'uyunawa', 'cardimiin', 'mislady9629', 'kwunminhee', 'hong._.ji3', 'ricarica__e', 'salon_de_bit', 'yallelee', 'll.sarah_land.ll', 'mariinthewonderland', 'wisdom_j', 'c.c_skyung', 'haha_jian_', 'drsoyoon', 'angelina_pengclub', 'masha_tory', 'su_k_kim', 'bhs_rin', 'swell_aimee', 'ssovelyz', '_c_e_1221', 'unique_natsu', '__lucky77__', 'helenyjkim', 'lyn_a.mom', 'claire.02.03', 'heo.o.o', '_seolvely_1619', 'hea.lina', 'yookseong_mwahanmwuroo', 'queenbiseong', 'young_claudialee', 'perfume1404', 'imrachelhan', 'sseun010', 'ung.2.gamdok', 'ryeoeun.kwon']



    # user_infos_list =user_infos_list[400:1000]
    ##2. 유저 분할
    total_user_infos_group = divide_user_infos_list(user_infos_list, group_size=1)
    print(len(total_user_infos_group))

    ##3. db 발송
    send_total_message(total_user_infos_group, text, project_name=project, proxy=proxy)
