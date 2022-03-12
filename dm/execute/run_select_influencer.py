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


INSTA_ACCOUNT_OBJ = m_instagram.InstaAccount(channel_name="instagram")
INSTA_ACCOUNT_OBJ.client_name = "admin_test"

username = None
max_messages_per_day = 5
account_setting_info_list = INSTA_ACCOUNT_OBJ.select_all_cookie_user(username=username, max_messages_per_day= max_messages_per_day)
for account in account_setting_info_list:
    print(account["username"], account["password"], account["last_login"])




