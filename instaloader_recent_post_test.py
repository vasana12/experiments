import time

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

def update_available():
    INSTA_ACCOUNT_OBJ = m_instagram.InstaAccount(channel_name="instagram")
    INSTA_ACCOUNT_OBJ.client_name = "admin_test"
    account_setting_info = INSTA_ACCOUNT_OBJ.update_available()
    return account_setting_info

def get_hashtag_bot(hashtag_name):
    account_setting_info = select_user(username="send_direct_items")
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


hashtag_name_list = ["여자데일리룩코디", "친환경인테리어","친환경가구","옷장정리","인테리어소품", "드레스룸가구"]
username_list = []

for hashtag_name in hashtag_name_list:
    hashtag_bot = get_hashtag_bot(hashtag_name)
    try:
        for idx, item in enumerate(hashtag_bot.get_posts_api_v3(next_page=None, next_max_id=None)):
            if idx > 5000:
                break
            if idx%500 == 0 and idx/500>0:
                time.sleep(60)
            print(hashtag_name, idx, item.shortcode, item.likes)
            username = item.user.get("username")
            if username in username_list:
                print(f"{username} 중복")
                continue
            username_list.append(username)
            payload.update(username=username,hashtag=hashtag_name)
            res = LAMBDA_CLIENT.invoke(FunctionName="user_brief_by_username", InvocationType="Event", Payload=json.dumps(payload))
        update_available()
    except Exception as e:
        print(e)
        continue
