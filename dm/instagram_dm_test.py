from db import m_instagram
from instamanager import Bot
db_conn = m_instagram.InstaDB().conn
INSTA_ACCOUNT_OBJ = m_instagram.InstaAccount(channel_name="instagram")
INSTA_ACCOUNT_OBJ.client_name = "admin_test"

login_account = INSTA_ACCOUNT_OBJ.load_cookie_user_and_update_status_to_login_dm(username="klejmushinakichesova")
username = login_account["username"]
password = login_account["password"]


# # username = 'sp22064497'
# # password = 'amdc2580!'
# # proxy = f"http://user-{username}-sessionduration-10:{password}@gate.smartproxy.com:10000"
# host = "residential.ipb.cloud"
# port = "7777"
# mobile_proxy_username = "customer-yxha19913701-asn-9158-sessid-TnHj-sesstime-30"
# mobile_proxy_password = "ywiB*20dC"
# proxy = f"http://{mobile_proxy_username}:{mobile_proxy_password}@{host}:{port}"
#
bot = Bot(db_conn=db_conn)
#
bot.login(username=username, password=password, proxy=None, session_info=login_account)

user_id_list = ["send_direct_items","send_direct_items","send_direct_items"]
# ## Message
#
text = "이 번호로 인증해 주세요: 99999111"
#
response = bot.send_messages(text, user_id_list)
print(response)