from db import m_instagram
from dm.engine import completed_target_influencer
from instamanager import Bot
import logging
from dm.prepare import get_dm_source, get_influencer
from instagrapi import Client

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
    # username, password = 'datacast1', 'amdc2580!'
    # proxy = f"http://user-{username}-sessionduration-1:{password}@us.smartproxy.com:10001"
    # proxy = "http://5rfpjo4evhm0c8dx:ihzoneqam4p3vt2b@texas1.thesocialproxy.com:10000"

    ### 0. 세팅 : 프로젝트, 발송 텍스트, 프록시
    project = "golf"
    start_date = "2022-08-18"
    project_info = {"project_name":project, "start_date": start_date}

    """ dm/source/message """
    text = get_dm_source.get_source_message(filename="golf.txt")
    host, port, mobile_proxy_username, mobile_proxy_password = "resi3.ipb.cloud", "9000", "MrIlCvzYImHc0I3t", "wifi;us;;;;"
    proxy = f"http://{mobile_proxy_username}:{mobile_proxy_password}@{host}:{port}"
    #
    # proxy = None
    ### 1. 전송할 인플루언서 리스트 가져오기
    """ dm/source/hashtag """
    black_list = completed_target_influencer.find_completed_influencer(project_name=project)
    target_username_list = [50816550720, 1571030083, 39808133809, 3237862724, 50811647885, 47534307465, 8305241127, 7729375430, 46660238788, 1808223166, 12088169226, 1398053232, 37060671597, 1268586135, 12088169226, 3450249320, 30981995142, 4941520458, 5390542355, 47814402749, 402694031, 45253200008, 47221287103, 50404645796, 3854545177, 5553929483, 4709242352, 49388377091, 2786100181, 7086110788, 2282510817, 3531616602]
    # target_username_list = list(set(target_username_list) - set(black_list))
    target_username_list = target_username_list[0:4]
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


        client = Client(proxy=proxy)
        client.login(username=username, password=password)
        client.direct_send(text=text, user_ids=target_username_list)

        # target_username_list = broken_items
        # logger.info(f"broken_target_username_list:{target_username_list[0:10]}")
        #
        # if not broken_items:
        #     logger.info(f"no target_username_list ")
        #     break

if __name__ == "__main__":
    run()

