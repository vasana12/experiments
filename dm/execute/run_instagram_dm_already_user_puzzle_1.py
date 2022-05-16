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
    project = "puzzle"
    start_date = "2022-05-16"
    project_info = {"project_name":project, "start_date": start_date}

    """ dm/source/message """
    text = get_dm_source.get_source_message(filename="puzzle_pet.txt")
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
    target_username_list = ['hwangbo_eon', 'somino_myowon', 'reuming5', 'pet3l', 'mippeuda15', '_bbmom_', 'qlscmwlgp', '73joo', '3dogs_mommy_', 'straydogsss', 'challenginghaha', 'jiny1979', 'food_gj', 'inssa_elf', 'bds_3dogs', 'bebi_pet1', 'hanorhanor', 'beombi_sodam_homerun', 'myunga.mom', 'bbobbo.y', '2020kokos', 'sooaini', 'dareum_tv', 'oki_roki', 'song.dajung', 'pet_allowed_korea', '5417515wr', 'jjang_a_som', 'lychee_409', 'per0e0', 'heo.jiwoo', 'ranimandoo', 'doong_chi', 'shl20233_', 'byulhana73', 'nana6140', 'hyejing_gram', 'hyejin_jun', 'jade___y', 'jam_jam_4.1', 'medu435', 'oreo_20.08.20', '_teri_baekho', 'yangsisters3133', 'tteokguk_nuna_official', 'bluepumpkin1', 'ocaoboe20', 'noridongsan', 'dannyxoh', 'jrong.__', 'stylist.sooa', 'soo.sunni', 's0.__.s2', 'jjeonda.ne', 'phantompoodle.b', 'yj.__.94', 'kpetfair', 'a_club_moss', 'latte._.mitte', 'choregina', 'daondaonhae', 'tiareisle', 'subinkoh', 'ssoroo', 'groo.mingday', 'mr.popular__', 'mignon_bonbon_lovely', 'danchu0', 'luckyboxy7', 'luv_sky37', 'urban192', 'cat.leo.bkk', 'ruinism17', 'harumi_hhy', 'chamcheeflix', 'haul711', 'taeyul_7', 'nabijou1004', 'cat_and_cat_house', 'bominmonkey', 'kirin_makeup', 'anse1114', 'a_family17', 'parrot.boss', 'mukbang_azzi', 'zayeun', 'vets60', 'slowgo__', 'chundung_mama', 'byhjwh', 'pomi_0530', 'a_family17', 'fluffy_petstylist', 'corgi_danchoo', 'mjinmyheart23', 'cat._.angry', 'visoop', 'leeyoung102', 'wooreewooree', 'worldstar_saemprince']
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

