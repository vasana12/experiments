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
    project = "cake"
    start_date = "2022-05-19"
    project_info = {"project_name":project, "start_date": start_date}

    """ dm/source/message """
    text = get_dm_source.get_source_message(filename="cake.txt")
    host,port, mobile_proxy_username,mobile_proxy_password = "residential.ipb.cloud", "7777", "customer-lsgr20040901-asn-12576-sessid-xnoa-sesstime-1", "UG2xaDXxC"
    proxy = f"http://{mobile_proxy_username}:{mobile_proxy_password}@{host}:{port}"
    #
    # proxy = None

    ### 1. 전송할 인플루언서 리스트 가져오기
    """ dm/source/hashtag """
    search_hashtag = get_dm_source.get_source_hashtag("cake.txt")
    search_filter = {"$text": {"$search": search_hashtag}}
    collection_name = "user_checkpoint"
    file_name, skip, limit, only_username, = search_hashtag, 0, 100, False
    target_username_list = get_influencer.main(search_filter=search_filter, file_name=file_name, skip=skip, limit=limit,
                                               only_username=only_username, collection_name=collection_name)
    target_username_list = list(map(lambda x: x["username"], target_username_list))
    #

    ## 2. 이전 프로젝트 에서 진행한 인플루언서 제외하기
    target_username_list = ['blessing__cake', 'seongeun99con', 'lovely__soyul_', 'jhee0_o', 'luka511_seoul', '22.14_s', 'oneday__sunday', 'yenas_cake', 'lazybutter_', 'induck._.joha', 'subingim787', 'queensberryshop', 'awesome.feels', 'lololocake', 'dsstudio__', '_adorok', '2097_kid', '4.17g', 'iam.coma', '1ov.hy', 'zuyomi_', 'j_cake94', 'gyeong_a_park', '__ssong__cake', 'mik_bread', 'circus_rabbit_', 'cake.dew', 'sorok_sorok_', 'wony25', 'fineapple._.shop', 'the_young.123', 'konga_topper', 'i_light_u_', 'malorenzaricafrente', 'jaejinjang', 'cakeswaysydney', 'happy_birthcake', 'blue_blue_no1', 'lette_coffee', 'cafe_botongdays', 'toanne__', '_azure_20', 'cafe.from_here', 'iyeonggil41', 'kombuccombu', 'guksatchi1023', 'kimhyesong', 'bonnie_guk87', 'thejumcake_list', 'lhy1948lhy', 'familia_cafe_namhae', 'shineshine_diana', 'chorokcake_', 'aiiino_rose18', 'liams_cakery', 'cakeson8', 'la_touchante', 'mini0.0n', 'janeuk_the_bake', 'ssu8849', 'sweetmeup_cake', 'chumily_studio', 'creampalette_korea', 'lemon_sorbetb', 'sara459268', 'cafe_ilgiyebo', 'minngkik', 'ggum_cake', 'jiji.0609', 'dabang_92', 'beros2548', 'mrleonardjejudo', 'miggang4', 'cafe_dal_com', 'ba_bameee', 'minari_sa', 'milo__cake', 'thats_light_', 'jenyinny', 'package_factory', 'ddoe_candle', 'wis_baking22_', 'amor_bread', 'ummmicake', 'emilyblack902', 'kikine_cake_', 'cake.herenow', 'amoimoii', 'mama_love_pie', 'mooming_cake', 'i_like_cake79', 'y.j__cake_o_o', 'hhhaaa_e', 'tutti___cake', 'oftheday_cafe', 'blumen_cake', 'kkk_jh.o7', 'momo_keki', 'edel_rice', 'iji_cake', 'aindain7', 'seorae_cake', 'eun.uuuuu', 'the_sweet_bar_seoul', 'kkotchaeum_cake', 'awesome__cake_', 'the_bliss_cake', 'yuil879', 'cookie___yum', 'ku_mba_horse', 'snow_palette', 'oilieli.studio.bkk', 'kifkif.official', 'wooriflowercake', 'party_factory_2019', 'seogwipean_cake', '_yonghs_0925', '_stellaxx_26', 'pawty_bakeshop', 'seoyike', '_dcake', 'heohwatree_cake', 'soyang_tyrano', 'g.r.e.e.m', 'izitmagazine', 'yy_eong_2', 'rafre_fruit', 'the.dalda', 'sun_aous2', '0331_byul', 'mariaabraham188', 'bellawilkins825', 'ivonamironova3', 'anzhelafedorova7723', 'wizgram_up', 'dianerutherford236', 'vinewiz_mkte', 'vinewiz_mktb', 'mariannaiashina82', 'ilonazharkova1', 'afanasevaemeliana', 'btgram.a', 'ioannashestakova5', 'leevely_cake', 'made_by_wonjung', 'kalanchoe_d.cake', 'cafe_cakie', 'mr__jang', 'lenede_dessert', 'ssy6777']


    black_list = completed_target_influencer.find_completed_influencer(project_name=project)
    # target_username_list = list(set(target_username_list) - set(black_list))
    logger.info(f"총 {len(target_username_list)} 명에게 dm 발송 시작 target_username_list:{target_username_list}")

    while True:
        max_messages_per_day = 10
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

