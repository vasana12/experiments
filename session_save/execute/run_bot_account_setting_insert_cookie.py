from datetime import datetime
from pathlib import Path
import logging
from db import m_instagram
from session_save.setting.botAccount_setting_db import read_account_setting_info_from_db, save_uuid_and_session_info, update_account_unavailable

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
    source_path = parent.joinpath("source", "login_test_account.txt")
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
            info = login_account_info.split("||")
            info_login = info[0].split(":")

            username, password = info_login[0], info_login[1]
            info_cookie = info[1]
            info_cookie = info_cookie.split(" ")
            device_id = info_cookie[0].split(";;")[0]
            advertising_id = info_cookie[0].split(";;")[1].split(";")[0]
            phone_id = info_cookie[0].split(";;")[1].split(";")[1].split("|")[0]

            setting_info = read_account_setting_info_from_db(username=username,password=password)

            setting_info["username"] = username
            setting_info["password"] = password
            setting_info["uuids"]["phone_id"] = phone_id
            setting_info["uuids"]["device_id"] = device_id
            setting_info["uuids"]["advertising_id"] = advertising_id

            setting_info["cookie"] = {}
            setting_info["cookie"]["ig_did"] = info[1].split("ig_did=")[1].split(";")[0]
            setting_info["cookie"]["ig_nrcb"] = info[1].split("ig_nrcb=")[1].split(";")[0]
            setting_info["cookie"]["mid"] = info[1].split("mid=")[1].split(";")[0]
            setting_info["cookie"]["csrftoken"] = info[1].split("csrftoken=")[1].split(";")[0]
            setting_info["cookie"]["sessionid"] = info[1].split("sessionid=")[1].split(";")[0]
            setting_info["cookie"]["ds_user_id"] = info[1].split("ds_user_id=")[1].split(";")[0]
            setting_info["cookie"]["rur"] = info[1].split("rur=")[1].split(";")[0]
        except Exception as e:
            logger.error(f"insert error - {e}/ {idx} - username:{username}/password:{password} registered error")
        else:
            logger.info(f"{idx} - username:{username}/password:{password} registered new!")
            save_uuid_and_session_info(setting_info=setting_info)

if __name__ == "__main__":
    insert_account()