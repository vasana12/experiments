import json
from datetime import datetime
from pathlib import Path
import logging
from db import m_instagram
import base64
from session_save.setting.botAccount_setting_db import read_account_setting_info_from_db, save_uuid_and_session_info, save_uuid_and_session_info_bandncast,update_account_unavailable
import ast
insta_db = m_instagram.InstaDB(db_name="account")

FORMAT = '%(module)s.%(funcName)s - %(message)s - %(levelname)s - %(asctime)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)
if logger.hasHandlers():
    # Logger is already configured, remove all handlers
    logger.handlers = []
logger.setLevel(logging.INFO)

def read_account_info_from_text():
    parent = Path.cwd().parent
    source_path = parent.joinpath("source", "login_test_account_cookie.txt")
    login_account_file = source_path.open("r")
    login_account_info_list = login_account_file.read().splitlines()

    return login_account_info_list

def insert_account():
    logger.debug("insert_account_start")
    login_account_info_list = read_account_info_from_text()

    seller = "insta_web"
    client_name = "admin_test"
    account_collection = None
    for idx, login_account_info in enumerate(login_account_info_list):
        username , password = None, None
        if login_account_info == "":
            continue

        try:
            info = login_account_info.split("|")
            account_info = info[0].split(":")

            username = account_info[0]
            password = account_info[1]

            csrftoken = login_account_info.split("csrftoken=")[1]
            csrftoken = csrftoken.split(";")[0]

            ds_user_id = login_account_info.split("ds_user_id=")[1]
            ds_user_id = ds_user_id.split(";")[0]

            sessionid = login_account_info.split("sessionid=")[1]
            sessionid = sessionid.split(";")[0]
            sessionid = sessionid.split("||")[0]

            # rur = login_account_info.split("rur=")[1]
            # rur = rur.split(";")[0]
            setting_info = read_account_setting_info_from_db(username=username, password=password)

            setting_info["username"] = username
            setting_info["password"] = password
            setting_info["cookie"] = {}
            setting_info["cookie"]["csrftoken"] = csrftoken
            setting_info["cookie"]["sessionid"] = sessionid
            setting_info["cookie"]["ds_user_id"] = ds_user_id
            setting_info["cookie"]["rur"] = "AG"
        except Exception as e:
            try:
                logger.info(f"{idx} - username:{username}/password:{password} error registered error!")
                info = login_account_info.split("||")
                username = info[0].split(":")[0]
                password = info[0].split(":")[1]

                cookie_info = info[1]
                csrftoken = cookie_info.split("csrftoken=")[1]
                csrftoken = csrftoken.split(";")[0]

                ds_user_id = cookie_info.split("ds_user_id=")[1]
                ds_user_id = ds_user_id.split(";")[0]

                sessionid = cookie_info.split("sessionid=")[1]
                sessionid = sessionid.split(";")[0]

                mid = login_account_info.split("mid=")[1]
                mid = mid.split(";")[0]

                rur = cookie_info.split("rur=")[1]
                rur = rur.split(";")[0]

                setting_info = read_account_setting_info_from_db(username=username, password=password)
                setting_info["username"] = username
                setting_info["password"] = password
                setting_info["cookie"] = {}
                setting_info["cookie"]["mid"] = mid
                setting_info["cookie"]["csrftoken"] = csrftoken
                setting_info["cookie"]["sessionid"] = sessionid
                setting_info["cookie"]["ds_user_id"] = ds_user_id
                setting_info["cookie"]["rur"] = rur

                logger.info(f"ex1 {idx} - username:{username}/password:{password} error registered new!")
            except:
                logger.error(f"insert error 2 - {e}/ {idx} - username:{username}/password:{password} registered error")
                info = login_account_info.split("|")
                account_info = info[0].split(":")

                username = account_info[0]
                password = account_info[1]

                user_agent = info[1]

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
                setting_info["cookie"]["csrftoken"] = csrftoken
                setting_info["cookie"]["sessionid"] = sessionid
                setting_info["cookie"]["ds_user_id"] = ds_user_id
                setting_info["cookie"]["rur"] = rur
                save_uuid_and_session_info(setting_info=setting_info, seller=seller, client_name=client_name, account_collection=account_collection)
                logger.info(f"{idx} - username:{username}/password:{password} error registered new!")
        else:
            logger.info(f"here 3 {idx} - username:{username}/password:{password} registered new!")
            save_uuid_and_session_info(setting_info=setting_info, seller=seller, client_name=client_name, account_collection=account_collection)
if __name__ == "__main__":
    insert_account()