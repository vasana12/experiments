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
    account_setting_info = INSTA_ACCOUNT_OBJ.select_cookie_user_v1(username=username, max_messages_per_day= max_messages_per_day)
    return account_setting_info
#
def run():
    username, password = 'sp22064497', 'amdc2580!'
    # proxy = f"http://user-{username}-sessionduration-1:{password}@us.smartproxy.com:10000"
    # proxy = "http://5rfpjo4evhm0c8dx:ihzoneqam4p3vt2b@texas1.thesocialproxy.com:10000"

    ### 0. 세팅 : 프로젝트, 발송 텍스트, 프록시
    project = "taewha"
    start_date = "2022-03-12"
    project_info = {"project_name":project, "start_date": start_date}

    """ dm/source/message """
    text = get_dm_source.get_source_message(filename="cook.txt")
    host,port, mobile_proxy_username,mobile_proxy_password = "residential.ipb.cloud", "7777", "customer-lsgr20040901-asn-20057-sessid-pCMf-sesstime-1", "UG2xaDXxC"
    proxy = f"http://{mobile_proxy_username}:{mobile_proxy_password}@{host}:{port}"
    #
    # proxy = None
    ### 1. 전송할 인플루언서 리스트 가져오기
    """ dm/source/hashtag """
    search_hashtag = get_dm_source.get_source_hashtag("taewha.txt")
    print(search_hashtag)
    search_filter = {
        "user_followed_by": {"$gte": 3000},
        "$text": {"$search": search_hashtag}
    }

    file_name, skip, limit, only_username,  =  search_hashtag, 0, 3000, False
    # target_username_list = get_influencer.main(search_filter=search_filter, file_name=file_name, skip=skip, limit=limit, only_username=only_username)
    # target_username_list = list(map(lambda x: x["username"], target_username_list))

    ## 2. 이전 프로젝트 에서 진행한 인플루언서 제외하기
    # black_list = completed_target_influencer.find_completed_influencer(project_name=project)
    target_username_list =['iam_beautifulstar', 'greedeat', 'inssa_elf', 'minahjjang', 'sh1016sh', '_hyerim.2', 'lym1004567', 'blue8854', 'incheon_all', 'kingo1398', 'mhhan71', 'haebbang2', 'kimming_gu', 'jinyzzac', 'bijou_table_', 'insight_food', 'taki1471', 'dd__boon', 'lsb_9225', 'hanna199612', 'ram._.0203', 'toyluv_', 'sujung767676', 'se6323321', 'seraspia', 'heeya_xxi', 'gabriella_chae', 'love.1002', 'jjuaeng2', 'skyyouli23', 's_euun_', 'khccsj1', 'haram2ne', 'lin________2', 'bomnal_hy', '96_c.s', 'ssamji36', 'kwonhuira', 'fandatoy', 'nabong_cafe', 'myvely828', '_yeolmae_', 'dxyxn___', 'hsw6767', 'lee_a.ra', 'hanaplusu', 'h.m_cooking_mom', 'anniemom89', 'wonderkkakka', 'yerim.jin', 'poodlegguggu_', 'gyungsss', 'haitai_co', 'bora.own', 'hi_ggung', 'water.eun', 'eh__kkk', 'yoons_eatrip', 'metal_kro', 'yulcongcong', 'star0k77', 'mirang_yerang', 'kyung_a_choi', 'jobsick_eat', 'dachshund_robin', '2at_ing_k', 'ruiyan1024', 'dkfnsl1987', 'bbobbo.y', 'humor_lovely', 'han_rabongri', '___cute._.cute___', 'woongjinfood', 'poorin_diary', 'star279600', 'bn_07.07', 'yoonminjeon', 'paldofood', 'nyxseren', 'yeminhye', 'mukmuk_ga', 'kimsumi35', 'im__eunsol', 'b3game5242', 'touslesjours_kr', 'hongz_zi', 'inssa_bro', 'dolmaengyi_', 'k___soo_ah', 'bbang0123_', 'milk_hodu', 'kim_____pink', 'peki_kkong', 'heeee.eee', 'davely1013', 'i._.morae', 'dogistar_jk', 'im.simba_nala', 'ziny_ee', 'h_gail95', 'likesugi', 'jeehyeounn', 'doctordog_korea', 'i_am_deoksun', 'mytinylittle_aari', 'kyung_hee2994', 'joohee0630', 'imall1028', 'do_boo_diary', '_mieumi', 'nemo.tattoo', 'ji_jiji03', 'luie_petfood', 'meongdi_', 'soon.doong', 'the_jaehee', 'giant_baking', 'nachokancho', '_yo_cook_', 'chulsoo_dog']
    black_list = ['greedeat', 'inssa_elf', 'incheon_all', 'insight_food', 'dd__boon', 'gabriella_chae', 'jjuaeng2', 'haram2ne', 'fandatoy', 'dxyxn___', 'lee_a.ra', 'anniemom89', 'wonderkkakka', 'poodlegguggu_', 'gyungsss', 'haitai_co', 'bora.own', 'hi_ggung', 'water.eun', 'eh__kkk', 'jobsick_eat', 'dachshund_robin', '2at_ing_k', 'bbobbo.y', 'humor_lovely', 'han_rabongri', '___cute._.cute___', 'woongjinfood', 'poorin_diary', 'bn_07.07', 'paldofood', 'touslesjours_kr', 'hongz_zi', 'inssa_bro', 'dolmaengyi_', 'k___soo_ah', 'bbang0123_', 'milk_hodu', 'peki_kkong', 'heeee.eee', 'dogistar_jk', 'im.simba_nala', 'ziny_ee', 'doctordog_korea', 'i_am_deoksun', 'mytinylittle_aari', 'do_boo_diary', '_mieumi', 'nemo.tattoo', 'ji_jiji03', 'luie_petfood', 'meongdi_', 'soon.doong', 'the_jaehee', 'giant_baking', 'nachokancho', '_yo_cook_', 'chulsoo_dog']
    target_username_list = list(set(target_username_list) - set(black_list))
    # target_username_list = []
    logger.info(f"총 {len(target_username_list)} 명에게 dm 발송 시작 target_username_list:{target_username_list}")
    if len(target_username_list) == 0:
        logger.info(f"인플루언서가 존재하지 않습니다.")
        return

    while True:
        max_messages_per_day = 5
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

