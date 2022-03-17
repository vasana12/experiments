import time
from datetime import datetime
from datetime import timedelta
import logging
from db import m_instagram
from session_save.util import generate_uuid

insta_db = m_instagram.InstaDB(db_name="account")
account_collection = insta_db.account_collection

FORMAT = '%(module)s.%(funcName)s - %(message)s - %(levelname)s - %(asctime)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)
if logger.hasHandlers():
    # Logger is already configured, remove all handlers
    logger.handlers = []
logger.setLevel(logging.DEBUG)


SERVICE_INSTAGRAM = m_instagram.InstaDB(db_name="service_instagram").db
INSTA_ACCOUNT_OBJ = m_instagram.InstaAccount(client_name="admin", channel_name="instagram").db
ACCOUNT_COLLECTION = INSTA_ACCOUNT_OBJ['account']
BAND_ACCOUNT, HASHTAG_AND_USER, PROJECT_COLLECTION, ITEM_HASHTAG_COLLECTION, ITEM_USER_COLLECTION, ITEM_LOCATION_COLLECTION, INFO_COLLECTION, TASK_COLLECTION, POST_COLLECTION, SEARCH_COLLECTION, SETTING_COLLECTION = \
    SERVICE_INSTAGRAM["account_instagram"], SERVICE_INSTAGRAM["hashtag_and_user"], SERVICE_INSTAGRAM["project"], SERVICE_INSTAGRAM["hashtag"], \
    SERVICE_INSTAGRAM["user"], SERVICE_INSTAGRAM["location"], SERVICE_INSTAGRAM["info"], SERVICE_INSTAGRAM["task"], \
    SERVICE_INSTAGRAM["post"], SERVICE_INSTAGRAM["search"], SERVICE_INSTAGRAM["setting"]

def calcuate_check_point_deadline():
    check_point_deadline = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=4)
    return check_point_deadline

def update_account_unavailable(username):
    update_filter = {"username":username}
    update = {"$set":{"status":"unavailable"}}
    ACCOUNT_COLLECTION.update_one(filter=update_filter,update=update)

def read_account_info_from_db():
    filter_new = {"status": "new", "client_name": "admin_test"}
    # filter_old = {"status":"available", "client_name":"admin_test","last_login":{"$lte":calcuate_check_point_deadline()}}
    # filter_checkpoint = {"status":"checkpoint_required"}

    setting_account_doc = list(ACCOUNT_COLLECTION.find({"$or":[filter_new]}))
    return setting_account_doc

def read_accoun_info_from_db_one(client_name=None):
    filter_new = {"status": "new"}
    if client_name:
        filter_new.update(client_name=client_name)
    # filter_old = {"status":"available", "client_name":"admin_test","last_login":{"$lte":calcuate_check_point_deadline()}}
    # filter_checkpoint = {"status":"checkpoint_required"}
    setting_account_doc = ACCOUNT_COLLECTION.find_one_and_update({"$or":[filter_new]},update={"$set":{"status":"new"}})
    # setting_account_doc = list(ACCOUNT_COLLECTION.find({"$or":[filter_new]}))
    return setting_account_doc

def save_uuid_and_session_info(setting_info):
    account_info = account_collection.find_one(filter={"username":setting_info["username"]})

    ## when account_already exist
    if account_info:
        _id = account_info["_id"]
        account_collection.update_one(
            filter={
                "_id": _id
            },
            update={
                "$set": {
                    "usage.hashtag": 0,
                    "usage.dm": 0,
                    "last_login": datetime.now(),
                    "status": "available",
                    "uuids": setting_info["uuids"],
                    "timing_value.last_login": time.time(),
                    "timing_value.last_experiments": time.time(),
                    "device_settings": setting_info["device_settings"],
                    "user_agent": setting_info["user_agent"],
                    "session": setting_info["cookie"],
                    "mobile_session": True
                }
            }
        )
        return

    ### new account setting info insert
    insert_info = {
        "username": setting_info["username"],
        "password": setting_info["password"],
        "client_name": setting_info["client_name"],
        "channel": "instagram",
        "status":"available",
        "limit": {
            "dm": setting_info["limit"]["dm"],
            "hashtag": setting_info["limit"]["hashtag"]
        },
        "usage": {
            "dm": 0,
            "hashtag": 0
        },
        "uuids":setting_info["uuids"]
            ,
        "timing_value":
            {
                "last_login": time.time(),
                "last_experiments": time.time()
            },
        "device_settings": setting_info["device_settings"],
        "user_agent": setting_info["user_agent"],
        "session": setting_info["cookie"],
        "mobile_session" :True,
        "last_login": datetime.now(),
    }

    account_collection.insert_one(insert_info)

def read_account_setting_info_from_db(username, password):
    uuids = generate_uuid.generate_all_uuids(username, password)
    device_doc = SETTING_COLLECTION.find_one({"name":"base"})
    device_doc["uuids"] = uuids["uuids"]
    return device_doc

def read_challenge_required_account_info_from_db():
    filter_challenge = {"status": "challenge_required"}
    account_doc = list(ACCOUNT_COLLECTION.find(filter_challenge))
    return account_doc