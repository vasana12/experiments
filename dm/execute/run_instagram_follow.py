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

def select_user(username,max_messages_per_day):
    account_setting_info = INSTA_ACCOUNT_OBJ.select_cookie_user_v1(username=username, max_messages_per_day= max_messages_per_day)
    return account_setting_info

db_conn = m_instagram.InstaDB().conn
INSTA_ACCOUNT_OBJ = m_instagram.InstaAccount(channel_name="instagram")
INSTA_ACCOUNT_OBJ.client_name = "admin_test"

username, password = 'sp22064497', 'amdc2580!'
proxy = f"http://user-{username}-sessionduration-1:{password}@us.smartproxy.com:10000"

username = "imdwnnraknufcckfiy"
password = "u6ifI7j"
account_setting_info = select_user(username=None, max_messages_per_day= None)
bot = Bot(db_conn=db_conn)
bot.login(username=username, password=password, account_setting_info=account_setting_info, proxy=None, project_info =None)
influencer_list = ["dutohappy7", "bjin86", "dlwlrma"]
bot.follow_users(influencer_list)

