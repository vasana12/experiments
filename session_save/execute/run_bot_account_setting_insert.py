from datetime import datetime
from pathlib import Path
import logging
from db import m_instagram

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
    seller = "insta_shop"
    for idx, login_account_info in enumerate(login_account_info_list):
        if login_account_info == "":
            continue

        username = None
        password = None
        client_name = "admin_test"

        if login_account_info == "":
            continue

        try:
            info = login_account_info.split(":")
            username = info[0].replace(" ", "")
            password = info[1].replace(" ", "")
            password = password.split("|")[0]
            filter = {"username": username}
            update_data = {
                            "$set":
                                {
                                    "last_login": datetime.now(),
                                    "seller": seller,
                                    "status": "available",
                                    "client_name": client_name,
                                   "password": password,
                                },
                                    "$setOnInsert":
                                {
                                    "username": username,
                                    "channel": "instagram",
                                    "limit":
                                        {
                                            "dm": 10,
                                            "hashtag" : 1000
                                        },
                                    "usage":
                                        {
                                            "dm": 0,
                                            "hashtag": 1000
                                        }
                                }
                            }
            account_collection.update_one(filter=filter, update=update_data, upsert=True)
        except Exception as e:
            logger.error(f"insert error - {e}/ {idx} - username:{username}/password:{password} registered error")
        else:
            logger.info(f"{idx} - username:{username}/password:{password} registered new!")

if __name__ == "__main__":
    insert_account()