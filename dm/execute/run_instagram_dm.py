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

text = get_dm_source.get_source_message(filename="taewha_message.txt")
def select_user(username,max_messages_per_day):
    account_setting_info = INSTA_ACCOUNT_OBJ.select_cookie_user(username=username, max_messages_per_day= max_messages_per_day)
    return account_setting_info
#
def run():
    username, password = 'sp22064497', 'amdc2580!'
    proxy = f"http://user-{username}-sessionduration-1:{password}@us.smartproxy.com:10000"
    # proxy = "http://5rfpjo4evhm0c8dx:ihzoneqam4p3vt2b@texas1.thesocialproxy.com:10000"

    ### 0. 세팅 : 프로젝트, 프록시
    project = "taewha"
    host,port, mobile_proxy_username,mobile_proxy_password = "residential.ipb.cloud", "7777", "customer-lsgr20040901-asn-20057-sessid-pCMf-sesstime-30", "UG2xaDXxC"
    # proxy = f"http://{mobile_proxy_username}:{mobile_proxy_password}@{host}:{port}"
    #
    # proxy = None
    ### 1. 전송할 인플루언서 리스트 가져오기
    search_hashtag = get_dm_source.get_source_hashtag("taewha.txt")
    search_filter = {"user_followed_by": {"$gte": 4000, "$lte": 10000}}

    file_name, skip, limit, only_username,  =  search_hashtag, 1000, 3000, False
    target_username_list = get_influencer.main(search_filter=search_filter, file_name=file_name, skip=skip, limit=limit, only_username=only_username)
    target_username_list = list(map(lambda x: x["username"], target_username_list))

    ## 2. 이전 프로젝트 에서 진행한 인플루언서 제외하기
    black_list = completed_target_influencer.find_completed_influencer(project_name=project)
    target_username_list = list(set(target_username_list) - set(black_list))
    logger.info(f"총 {len(target_username_list)} 명에게 dm 발송 시작 target_username_list:{target_username_list}")

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
        bot.login(username=username, password=password, account_setting_info=account_setting_info, proxy=proxy)
        broken_items = bot.send_messages(text, target_username_list)
        target_username_list = broken_items
        if not broken_items:
            logger.info(f"no target_username_list ")
            break

if __name__ == "__main__":
    run()

