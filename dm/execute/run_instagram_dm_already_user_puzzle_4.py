import time

from db import m_instagram
from dm.engine import completed_target_influencer
from instamanager import Bot
import logging
from dm.prepare import get_dm_source, get_influencer

FORMAT = '%(module)s.%(funcName)s - %(message)s - %(levelname)s - %(asctime)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)
if logger.hasHandlers():
    # Logger is already configured, remove all handlers
    logger.handlers = []
logger.setLevel(logging.INFO)



db_conn = m_instagram.InstaDB().conn
INSTA_ACCOUNT_OBJ = m_instagram.InstaAccount(channel_name="instagram")
INSTA_ACCOUNT_OBJ.client_name = "admin_test"



def select_user(username,max_messages_per_day):
    account_setting_info = INSTA_ACCOUNT_OBJ.select_cookie_user_v2(username=username, max_messages_per_day= max_messages_per_day)
    return account_setting_info
#
def run():

    ### 0. 세팅 : 프로젝트, 발송 텍스트, 프록시
    project = "replica"
    start_date = "2022-05-18"
    project_info = {"project_name":project, "start_date": start_date}

    """ dm/source/message """
    text = get_dm_source.get_source_message(filename="replica.txt")
    host,port, mobile_proxy_username,mobile_proxy_password = "residential.ipb.cloud", "7777", "customer-lsgr20040901-asn-12576-sessid-xnoa-sesstime-1", "UG2xaDXxC"
    proxy = f"http://{mobile_proxy_username}:{mobile_proxy_password}@{host}:{port}"
    #
    # proxy = None

    ### 1. 전송할 인플루언서 리스트 가져오기
    """ dm/source/hashtag """
    # search_hashtag = get_dm_source.get_source_hashtag("puzzle_pet.txt")
    # search_filter = {"$text": {"$search": search_hashtag}}
    # collection_name = "user_checkpoint"
    # file_name, skip, limit, only_username, = search_hashtag, 0, 100, False
    # target_username_list = get_influencer.main(search_filter=search_filter, file_name=file_name, skip=skip, limit=limit,
    #                                            only_username=only_username, collection_name=collection_name)
    # target_username_list = list(map(lambda x: x["username"], target_username_list))
    #

    ## 2. 이전 프로젝트 에서 진행한 인플루언서 제외하기
    target_username_list = ['acorns_muk', '__azure22', '777._.flower', '00.lja', 'woongpage', 'guccijjang97', 'you_want_ccichu', 'yeoniii_0_0', 'the_ssome', 'ss.o_nail', 'sehyun._.lee', 's2ooah', 'mozzi_guzzi', 'ming_kimberly1', 'maisonseowon', 'lovely._.hyunji', 'lil_uzin_vert', 'jacobsshq.wendy', 'i_vely___', 'hee.vely0', 'gucci_chanel_dior_3', 'giwon_97', 'genuino_2323', 'eun_gyeom_97', 'eeuuuna', 'daebak._.store1', 'bagdeogyong', 'artq_artq', 'allrps_wear', '____a_ko', '0hi1110', '0eun2222', 'yitaly_', 'dio_h92', '_tangerine_g', 'yeon._.xx98', 'sora1096', 'sakura_95s', 'sabirani___.bos', 'ot_bbal', 'ono_gucci', 'oooan_', 'muse_kji', 'meezzi_shop', 'lovely_wendy27', 'koojjipocha', 'ju.ceol', 'j_e_e.2', 'j.h0914', 'gimgucci', 'eunji_61', 'duk2__', 'dogamor_pet', 'da0_0e', 'bling__bae', '_shoppia', '97_01_09_', '50_again', 'babyxhyj', 'mmm__su', 'thisis_gucci_mozzi', 'sunshiiiiiiiin', 'sungjinoooo', 'su_daily_', 'straight_hyun', 'siso0621', 'shom_offwoney', 'shieldsqwe.priscilla', 'olivermuk.lucinda', 'morae0607', 'lovelyiu_', 'k_s2_jin', 'jung921126', 'juni1426_', 'jin_s_u_', 'jaybian_leather', 'innerhands', 'hun_g0', 'heylovelybella', 'habyjay', 'gajd_kg', 'g.dongsook', 'eurochic_official', 'bully_gucci__', 'baesoyul_if', 'asurabalbalta_project', '__heee_.q', '1_p03', '03_10__', 'olivibrator', 'leather._place', 'dladuddnr3', 'a_like_u', 'xxkki__', 'vivi.zeo', 'u._.sung_', 'sst_tuuddyy', 'soul_mate0602', 'sooomda', 'rlcks1008', 'rene120194', 'pp_sowon', 'na_mi_iii', 'my.room.co.kr', 'moonsp_b', 'moonsp_1004', 'miyayeah', 'milanese_ilsan', 'kwagheeseop', 'juwon_0o0', 'hani_roni_papa', 'gucci__kitten', 'gather_light', 'eeebbuzzi', 'cjcj39', 'byeongmin7315', 'brandmall5000', 'brandmall77', 'brandmall_601', '___taeke', '99_chihun', '00_je11y', 'julee__kim', 'lily_kang_', 'yeong8319', 'mui_lolo', 'carmang__', 'mmmmm0613', 'green._.bichon', 'zz_gnu', 'yomitree_', 'wooyeoung_j', 'www_mijin_com', 'ttori_s2', 'suyeon_repair', 'suseonjalhaneunjib', 'sailors_destiny', 'pyo1.011', 'oystarisland', 'newsredhat', 'mustblack0623', 'minambeauty', 'mihwa_land', 'merimeri.07', 'meflwk', 'luxe_favori', 'luminousoden', 'lucksmango', 'kkk.hhh1109', 'kj_hwan_99', 'kimminwoo0423', 'kim_siyeon0810', 'junnyboy__20', 'jogaeng_', 'jk_kim75', 'iufancom', 'irvinekidz', 'huli.fox', 'honiuby1', 'hj._s2', 'hanseunghee357', 'gucci190308', 'gimminhyi666', 'free_color.20', 'eunveee_', 'dojjng', 'dbf1', 'chjoooon', 'cch___5858', 'c._.eunee', 'blacklabel_2186', 'binscare_', 'ayalayai.marva', 'afakesong', '_myeong_hwa', '93kkkkkk', 'sgy9099', 'seungsang_0210', '2kyeong_pyo', 'seooo_ji', 'fdsfsadfdsafdsa343', 'zeonxeozen', 'yeon_way', 'y_yymi', 'wilderfiv.maxine', 'unni_shop17', 'theshop1004', 'timmy79_shin', 'therealgoduck', 'taeheum_kim_', 'subsub.2', 'stylelo_official', 'sso_yyou_', 'sphynx_guzzi', 'sori.yul', 'soowon1718', 'smileyell', 'shalala__kids']
    black_list = completed_target_influencer.find_completed_influencer(project_name=project)
    target_username_list = list(set(target_username_list) - set(black_list))
    logger.info(f"총 {len(target_username_list)} 명에게 dm 발송 시작 target_username_list:{target_username_list}")
    while True:
        max_messages_per_day = 50
        account_setting_info = select_user(username=None, max_messages_per_day= max_messages_per_day)
        if not account_setting_info:
            logger.info("no account available")
            break
        username = account_setting_info["username"]
        password = account_setting_info["password"]
        logger.info(f"select - {username}:{password}")

        bot = Bot(db_conn=db_conn, max_messages_per_day=max_messages_per_day)
        bot.login(username=username, password=password, account_setting_info=account_setting_info, proxy=proxy, project_info =project_info)
        broken_items = bot.send_messages(text, target_username_list)
        target_username_list = broken_items
        logger.info(f"broken_target_username_list:{target_username_list[0:10]}")
        if not broken_items:
            logger.info(f"no target_username_list ")
            break

if __name__ == "__main__":
    run()

