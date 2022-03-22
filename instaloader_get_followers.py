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

def get_profile_bot(profile_name=None):
    account_setting_info = select_user("flnrmxcuaqxkhfxvhb")
    account_username = account_setting_info.get("username")
    account_password = account_setting_info.get("password")

    print(f"{account_username}/{account_password} 로그인 시도")
    bot = instabot.Instabot()
    bot.login(user=account_username)

    profile_bot = instabot.Profile.from_username(context=bot.context, username=profile_name)

    return profile_bot


profile_name_list = ["faker"]
username_list = []
for profile_name in profile_name_list:
    profile_bot = get_profile_bot(profile_name)
    for idx, item in enumerate(profile_bot.get_followers()):
        print(profile_name, idx, item.username)
        # if username in username_list:
        #     print(f"{username} 중복")
        #     continue
        # username_list.append(username)
        # payload.update(username=username, hashtag=hashtag_name)
        # res = LAMBDA_CLIENT.invoke(FunctionName="user_brief_by_username", InvocationType="Event", Payload=json.dumps(payload))


