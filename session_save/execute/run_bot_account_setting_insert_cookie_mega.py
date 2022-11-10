import json
from datetime import datetime
from pathlib import Path
import logging
from db import m_instagram
import base64
from session_save.setting.botAccount_setting_db import read_account_setting_info_from_db, save_uuid_and_session_info_new, save_uuid_and_session_info, update_account_unavailable
import ast
insta_db = m_instagram.InstaDB(db_name="account")
account_collection = insta_db.account_collection

FORMAT = '%(module)s.%(funcName)s - %(message)s - %(levelname)s - %(asctime)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)
if logger.hasHandlers():
    # Logger is already configured, remove all handlers
    logger.handlers = []
logger.setLevel(logging.INFO)

JIN_INSTAGRAM = m_instagram.InstaDB(db_name="instagram_analysis").db
JIN_ACCOUNT = JIN_INSTAGRAM["account"]

SERVICE_INSTAGRAM = m_instagram.InstaDB(db_name="service_instagram").db
INSTA_ACCOUNT_OBJ = m_instagram.InstaAccount(client_name="admin", channel_name="instagram").db
ACCOUNT_COLLECTION = INSTA_ACCOUNT_OBJ['account']
BAND_ACCOUNT, HASHTAG_AND_USER, PROJECT_COLLECTION, ITEM_HASHTAG_COLLECTION, ITEM_USER_COLLECTION, ITEM_LOCATION_COLLECTION, INFO_COLLECTION, TASK_COLLECTION, POST_COLLECTION, SEARCH_COLLECTION = \
    SERVICE_INSTAGRAM["account_instagram"], SERVICE_INSTAGRAM["hashtag_and_user"], SERVICE_INSTAGRAM["project"], SERVICE_INSTAGRAM["hashtag"], \
    SERVICE_INSTAGRAM["user"], SERVICE_INSTAGRAM["location"], SERVICE_INSTAGRAM["info"], SERVICE_INSTAGRAM["task"], \
    SERVICE_INSTAGRAM["post"], SERVICE_INSTAGRAM["search"]


def read_account_info_from_text():
    parent = Path.cwd().parent
    source_path = parent.joinpath("source", "login_test_account_cookie.txt")
    login_account_file = source_path.open("r")
    login_account_info_list = login_account_file.read().splitlines()

    return login_account_info_list

def insert_account():
    logger.debug("insert_account_start")
    login_account_info_list = read_account_info_from_text()
    for idx, login_account_info in enumerate(login_account_info_list):

        username , password = None, None

        if login_account_info == "":
            continue

        try:
            login_account_info = login_account_info.replace(";ig_nrcb=1","")
            info = login_account_info.split("::|")
            account_info = info[0].split(":")
            username = account_info[0]
            password = account_info[1]

            user_agent = info[1].split("|")[0]
            cookie_info = info[1].split("|")[1]
            mid = cookie_info.split("mid=")[1]
            mid = mid.split(";")[0]

            ig_did = cookie_info.split("ig_did=")[1]
            ig_did = ig_did.split(";")[0]

            csrftoken = cookie_info.split("csrftoken=")[1]
            csrftoken = csrftoken.split(";")[0]

            ds_user_id = cookie_info.split("ds_user_id=")[1]
            ds_user_id = ds_user_id.split(";")[0]

            sessionid = cookie_info.split("sessionid=")[1]
            sessionid = sessionid.split(";")[0]

            rur = cookie_info.split("rur=")[1]
            rur = rur.split(";")[0]

            setting_info = read_account_setting_info_from_db(username=username,password=password)

            setting_info["username"] = username
            setting_info["password"] = password
            setting_info["user_agent"] = user_agent
            setting_info["cookie"] = {}
            setting_info["cookie"]["ig_did"] = ig_did
            setting_info["cookie"]["mid"] = mid
            setting_info["cookie"]["csrftoken"] = csrftoken
            setting_info["cookie"]["sessionid"] = sessionid
            setting_info["cookie"]["ds_user_id"] = ds_user_id
            setting_info["cookie"]["rur"] = rur

        except Exception as e:
            logger.error(f"insert error - {e}/ {idx} - username:{username}/password:{password} registered error")
            info = login_account_info.split("|")
            account_info = info[0].split(":")

            username = account_info[0]
            password = account_info[1]

            user_agent = info[1]

            mid = login_account_info.split("mid=")[1]
            mid = mid.split(";")[0]

            ig_did = login_account_info.split("ig_did=")[1]
            ig_did = ig_did.split(";")[0]

            csrftoken = login_account_info.split("csrftoken=")[1]
            csrftoken = csrftoken.split(";")[0]

            ds_user_id = login_account_info.split("ds_user_id=")[1]
            ds_user_id = ds_user_id.split(";")[0]

            sessionid = login_account_info.split("sessionid=")[1]
            sessionid = sessionid.split(";")[0]

            rur = login_account_info.split("rur=")[1]
            rur = rur.split(";")[0]
            setting_info = read_account_setting_info_from_db(username=username, password=password)

            setting_info["username"] = username
            setting_info["password"] = password
            setting_info["user_agent"] = user_agent
            setting_info["cookie"] = {}
            setting_info["cookie"]["ig_did"] = ig_did
            setting_info["cookie"]["mid"] = mid
            setting_info["cookie"]["csrftoken"] = csrftoken
            setting_info["cookie"]["sessionid"] = sessionid
            setting_info["cookie"]["ds_user_id"] = ds_user_id
            setting_info["cookie"]["rur"] = rur
            logger.info(f"{idx} - username:{username}/password:{password} error registered new!")
            save_uuid_and_session_info_new(setting_info=setting_info)
        else:
            pass
            logger.info(f"{idx} - username:{username}/password:{password} registered new!")
            input()
            save_uuid_and_session_info_new(setting_info=setting_info)
if __name__ == "__main__":
    insert_account()