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
    project = "re_model"
    start_date = "2022-06-21"
    project_info = {"project_name": project, "start_date": start_date}
    collection_name = "user_checkpoint"

    """ dm/source/message """
    text = get_dm_source.get_source_message(filename="model.txt")
    host, port, mobile_proxy_username, mobile_proxy_password = "residential.ipb.cloud", "7777", "customer-lsgr20040901-asn-12576-sessid-xnoa-sesstime-1", "UG2xaDXxC"
    proxy = f"http://{mobile_proxy_username}:{mobile_proxy_password}@{host}:{port}"

    # proxy = None
    ### 1. 전송할 인플루언서 리스트 가져오기
    """ dm/source/hashtag """
    search_hashtag = get_dm_source.get_source_hashtag("model.txt")
    black_list = completed_target_influencer.find_completed_influencer(project_name=project)
    search_filter = {"user_followed_by": {"$gte":500}, "$text":{"$search": search_hashtag}, "username":{"$nin": black_list}}

    file_name, skip, limit, only_username,  =  search_hashtag, 0, 100, False
    target_username_list = get_influencer.main(search_filter=search_filter, file_name=file_name, skip=skip, limit=limit, only_username=only_username, collection_name=collection_name)
    target_username_list = list(map(lambda x: x["username"], target_username_list))


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

