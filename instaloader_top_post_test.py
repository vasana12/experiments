import instabot
from db import m_instagram
import json
import boto3
import botocore.config
import logging

FORMAT = '%(module)s.%(funcName)s - %(message)s - %(levelname)s - %(asctime)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)
if logger.hasHandlers():
    # Logger is already configured, remove all handlers
    logger.handlers = []
logger.setLevel(logging.DEBUG)

cfg = botocore.config.Config(retries={'max_attempts': 0}, read_timeout=900000, connect_timeout=900000)
LAMBDA_CLIENT = boto3.client('lambda',
                             region_name='ap-northeast-2',
                             aws_access_key_id='AKIAYHHL7L4IP25TWTQQ',
                             aws_secret_access_key='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',
                             config = cfg)

payload = {"checkpoint_update_term": 0}

#
# response_payload = json.loads(res['Payload'].read().decode("utf-8"))
# print(response_payload)


INSTA_ACCOUNT_OBJ = m_instagram.InstaAccount(channel_name="instagram")
INSTA_ACCOUNT_OBJ.client_name = "admin_test"

def select_user(username=None):
    INSTA_ACCOUNT_OBJ = m_instagram.InstaAccount(channel_name="instagram")
    INSTA_ACCOUNT_OBJ.client_name = "admin_test"
    account_setting_info = INSTA_ACCOUNT_OBJ.select_cookie_user_v1(username=username)
    return account_setting_info

def get_hashtag_bot(hashtag_name):
    account_setting_info = select_user(username="seuwgaiwsjspdowinp")
    account_username = account_setting_info.get("username")
    account_password = account_setting_info.get("password")

    print(f"{account_username}/{account_password} 로그인 시도")
    bot = instabot.Instabot()
    bot.login(user=account_username)
    while True:
        try:
            hashtag_bot = instabot.Hashtag.from_name(context=bot.context, name=hashtag_name)
        except Exception as e:
            INSTA_ACCOUNT_OBJ.update_unavailable()
            print(e)
            continue
        else:
            return hashtag_bot


hashtag_name_list = ["P2E","NFT","비트코인", "playtoeran", "업비트", "엑시인피니티", "샌드박스", "메타버스", "게임", "돈버는게임", "부업", "빗썸", "모바일게임", "핸드폰게임"]
username_list = []
for hashtag_name in hashtag_name_list:
    hashtag_bot = get_hashtag_bot(hashtag_name)
    try:
        for idx, item in enumerate(hashtag_bot.get_top_posts_api_v3(next_page=None, next_max_id=None)):
            if idx > 3000:
                break
            print(hashtag_name, idx, item.shortcode, item.user, item.likes, item.next_page, item.next_max_id)
            username = item.user.get("username")
            if username in username_list:
                print(f"{username} 중복")
                continue
            username_list.append(username)
            payload.update(username=username,hashtag=hashtag_name)
            res = LAMBDA_CLIENT.invoke(FunctionName="user_brief_by_username", InvocationType="Event", Payload=json.dumps(payload))
    except Exception as e:
        print(e)
        continue

