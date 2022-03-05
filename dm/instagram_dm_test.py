from db import m_instagram
from instamanager import Bot
from pathlib import Path

project_dict = Path.cwd().parent
image_path = project_dict.joinpath("인스타그램_DM발송로고.png")

db_conn = m_instagram.InstaDB().conn
INSTA_ACCOUNT_OBJ = m_instagram.InstaAccount(channel_name="instagram")
INSTA_ACCOUNT_OBJ.client_name = "admin_test"

account_setting_info = INSTA_ACCOUNT_OBJ.load_cookie_user_and_update_status_to_login_dm(username="send_direct_items")

username = account_setting_info["username"]
password = account_setting_info["password"]

# # username = 'sp22064497'
# # password = 'amdc2580!'
# # proxy = f"http://user-{username}-sessionduration-10:{password}@gate.smartproxy.com:10000"
host = "residential.ipb.cloud"
port = "7777"
mobile_proxy_username = "customer-yxha19913701-asn-9158-sessid-TnHj-sesstime-30"
mobile_proxy_password = "ywiB*20dC"
proxy = f"http://{mobile_proxy_username}:{mobile_proxy_password}@{host}:{port}"

bot = Bot(db_conn=db_conn)
bot.login(username=username, password=password, account_setting_info= account_setting_info, proxy=None)
if bot.api.is_logged_in:
    print("login success")
user_id_list = ["volofodskijkibok"]
## Message

# text = "안녕하세요 반갑습니다"
bot.upload_photo(photo=str(image_path),caption="#강아지 #귀엽 #말티즈 #비숑")
# response = bot.send_messages(text, user_id_list)
# print(response)