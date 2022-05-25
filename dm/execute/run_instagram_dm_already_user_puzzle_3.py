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
    target_username_list = ['styleshop0066', 'styleshop216', 'styleshop1123', 'styleshop1127', 'yytuy1233', 'yunsook_1004', 'wyy12394', 'wook_pro_', 'tiannanda_w_shose2', 'sung_kyung_s2', 'styleshop1088', 'styleshop2222', 'styleshop1077', 'sswoon2017', 'ssong.s.home', 'srth4798sdrth2', 'speedgomtube', 'sofiashop77', 'snowtell309263', 'seojeong98', 'seo.bling', 'saundradunivan', 'riri___young', 'que_enestate', 'quyya960', 'luxe_club.0515', 'lovely_ellie_', 'love_lugu', 'lee_hm92', 'kimjunyoung1417', 'joo._.p', 'jjiiinn_2', 'jina_ne_shop', 'ji__dawn', 'jason_12375', 'incessantinability', 'imi_brandmall_dys', 'hyunjung_life', 'hwang_dave_7', 'hy____k', 'hootchuu', 'gvvbc326', 'guccccci_han', 'ginakuma1988232357', 'eve__adam._.v', 'eun.seo._', 'dolche9091', 'donghoon.js', 'don_the_who', 'dlwldms_0516', 'dianna__won', 'daily_13ear', 'classymall.vip', 'cine_21', 'cci_story', 'bombomnailbom', 'bless_haim', 'blisscatsbee', 'bingbingshop0', 'bin__e3', 'bichon_yeoreum2', 'barbiegirl_nail', 'actrob8554', '_sunny_0905', '_g2un', '__dropin', '___uk.ho', '90ju0', 'uiygo33', 'drimt00', 'xx.becky__', 'hyunggyu.baek', 's00_bin__', 'my_eternal_journey', 'waikiki___', 'beoy3976', 'hh_yyo', 'billionxor', '_ji_ni_world', 'seoul_bbans', 'eornappl', 'orcana_korea', 'timeplaza_', 'guzzi_buzzi', 'kkulbi1441', 'dfhbshnstgnjhfrtgnj', 'dzfnzdfgnzdfnbdzfn', 'star._.kkomi._.yomi', 'jeon.yuji', 'sfactory1', 'hamj_eojin', 'h__kyeong94', 'zheongzw', 'yeosu_j_nail', 'xoxo009400', 'vivid2204', 'vivid0091', 'uiui__vipmvp', 'sweet__bbo', 'sumfig2065499', 'strong_gunvely', 'stefaniemichova', 'sokuzaku1982384578', 'sb595959', 's_hyobi', 's9s9_222', 'ruby_inthecloset', 'rnmouvyz', 'rinsilver', 'raina0507.tw', 'oouu8787', 'oe.uni_', 'oh.week', 'ohmyshops_', 'nerveya694248', 'mustbeksy', 'moviebogo', 'moonjeongwon1994', 'moo_k.s', 'mitareha1972418581', 'luxurycoco880', 'luxuryham', 'logoshop0053', 'like_cocun', 'lauren.shop71', 'kuinshi1979264346', 'kosanpi1984242681', 'kirakira_ya', 'kidobai1974341815', 'junnnnil', 'jji11228', 'jihye_2415', 'jieunniiii', 'jew71799', 'hyebin3737', 'hello.9zzi', 'h22yaya', 'gucci_koreancat', 'gucci_ferret', 'gungsang2', 'ggim680', 'eve_h_ye', 'daikiri1971381509', 'dabin0218', 'comestyles', 'ch__da__mn', 'bundle_3205402', 'boutique_lucy3', 'bmsei_12', 'belmakang', 'beautiful_tiger_2020', 'bangmyeongbong2', 'aywhdk48', 'ajdtbsl4444', 'alizel_official', 'adsstt987', '_phd.d', '_kkang_1982', '98_nayuni__aa', '2__ug_', '1991_sole', '18mexceco', 'buddyye398853', 'ayoung_min', 'wwdkorea', 'haneulkim1217', 'silverain_3', 'yada.yadaa', 'giryboy', 't_an.na', 'gunh_0623', 'thunder132', 'zuyoni_._', 'znemio', 'yugyeong47', 'youngyeal.c', 'ymhj1031', 'xumeen', 'x_c_dahee', 'tae_mongdio', 'taeho_kim0128', 'sumin__b', 'strashop2021', 'starshop6333', 'stone_mina.ri', 'so._.yy04', 'shonminho', 's0n_n624', 'premiummultishop.gwangju', 'olimjho', 'noori_0311', 'noh_han_joon', 'modedetaillee666', 'minji_cho.oi', 'm.i_h.e.e', 'luxe_club.0828', 'lsyeon6469', 'lala_heeiii', 'kiyong_sin', 'k_yu_ju_', 'k647_4', 'jmg_267', 'jojigeun5', 'jjunghwany', 'j_dmerci', 'j.dauni', 'ishs2971', 'imsd92', 'imin._.ii', 'iiliiio', 'hyojeong_1225', 'hwaya_daaa', 'hn_77700', 'haenabbb', 'gottv28', 'etoile_1231', 'ebujang_lee', 'choongza', 'choi_mingji0_0', 'celecon_official', 'brownlabel_official', 'bellerue999', 'better_sy_', 'bean_look', 'amares119', 'allsnskorea', '_real_sound_20', '_inppyoo', '97_jae0', '900427s', '7cxk8od4', 'cheongchun_baeggwa', 'eldl_run', 'caroline_kyungyeon', '5.14kg._.kg', 'a.a___w.w', 'oouu2211', 'bombomcom1217', 'eyefull96', 'bts_dol_l', 'very_good_tip', 'staygold_ddyungi', 'yeazi__', 'mukizm', 'e.k0919', 'yessuru', 'nnnnnna_ni', 'optician.noon', 'silverpoodle.o_gucci', 's486je', 'lizh36', 'gim_min_jung__', 'g.seoju', 'seul_ki__i', 'zoddong', 'z._.hyun11', 'yusungwuk', 'youlisxx', 'yeowon_by_choi', 'yeoneeee_097', 'yeon____6814', 'yeon____82772', 'yeon____828812', 'yeon____1088', 'yeon____55711', 'yeon____108254', 'y__tg__', 'walter_kohi', 'valor3___', 'su__by__su', 'seul_latte', 'seokhocha', 'rogo.001', 'ralral_pan_love__', 'newturn_vip', 'morningstar6551', 'luv_gucci_20', 'leesihyeon_090901', 'kwark_hs', 'hyeseong__92', 'hye_rineee', 'hye_ji_nni', 'hhyebin._', 'golden___brush', 'epoi.italy', 'artesano_whee', 'amb_lee_dj', '1__masterpiece', '0_yereumi', 'veryverysun', 'zepeto.official', 'myeunji', 'in__sunny__', 'zzzung__2', 'chosemusa', 'vipmvp_2021', '2_jhyung', 'romi__shop_12', 'happyday_pury', 'guzzi_180107', 'haengja1114', 'young._.moonggu', 'yjlux_ceo', 'to.aarm', 'super._.gucci', 'ss__ss_ss__ss', 'shiba._.gucci', 'seungju_6686', 'seoook12', 'seokminn', 'rukawa_86', 'qshoppinggallery222', 'poni__zzang', 'noh.fe', 'my__gucci', 'mjrain6265', 'min.bora', 'lien_haha2', 'lee.ssosso', 'kkght5758', 'jiyeondeug3', 'jh____oo', 'jaye_0_n', 'jaetaeg_88996', 'j__921104', 'j2hwa', 'ian_sh_love', 'ije._.iyh', 'hyunisjjang', 'gugucci0218', 'goojji_ddeng', 'gimmijin3928', 'eileenlovesgucci', 'dinosaur_vivian', 'dayeol_k', 'daily_goni', 'carmel088', 'beak_sw', 'b.silver83', 'asd4062']
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

