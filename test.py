import instabot
from db import m_instagram
import json
import boto3
import botocore.config
import logging

INSTA_ACCOUNT_OBJ = m_instagram.InstaAccount(channel_name="instagram")
INSTA_ACCOUNT_OBJ.client_name = "admin_test"
account_setting_info = INSTA_ACCOUNT_OBJ.select_cookie_user_v1(username="send_direct_items")
account_username = account_setting_info.get("username")
account_password = account_setting_info.get("password")

bot = instabot.Instabot()
bot.login(user=account_username)
hashtag_name = "과일"
hashtag_bot = instabot.Hashtag.from_name(context=bot.context, name=hashtag_name)
for idx, item in enumerate(hashtag_bot.get_top_posts_api_v3(next_page=None, next_max_id=None)):
    if idx > 5000:
        break
    print(hashtag_name, idx, item.shortcode, item.user, item.likes, item.next_page, item.next_max_id)
