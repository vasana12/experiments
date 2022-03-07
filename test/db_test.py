from datetime import datetime
from datetime import timedelta
import logging
from db import m_instagram
from session_save.util import generate_uuid

insta_db = m_instagram.InstaDB(db_name="account")
account_collection = insta_db.account_collection

logger = logging.getLogger(__name__)

# 로그의 출력 기준 설정
logger.setLevel(logging.DEBUG)

# log 출력 형식
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s %(funcName)s - %(message)s')

# log 출력
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

JIN_INSTAGRAM = m_instagram.InstaDB(db_name="instagram_analysis").db
JIN_ACCOUNT = JIN_INSTAGRAM["account"]

SERVICE_INSTAGRAM = m_instagram.InstaDB(db_name="service_instagram").db
INSTA_ACCOUNT_OBJ = m_instagram.InstaAccount(client_name="admin", channel_name="instagram").db
ACCOUNT_COLLECTION = INSTA_ACCOUNT_OBJ['account']
BAND_ACCOUNT, HASHTAG_AND_USER, PROJECT_COLLECTION, ITEM_HASHTAG_COLLECTION, ITEM_USER_COLLECTION, ITEM_LOCATION_COLLECTION, INFO_COLLECTION, TASK_COLLECTION, POST_COLLECTION, SEARCH_COLLECTION, SETTING_COLLECTION = \
    SERVICE_INSTAGRAM["account_instagram"], SERVICE_INSTAGRAM["hashtag_and_user"], SERVICE_INSTAGRAM["project"], SERVICE_INSTAGRAM["hashtag"], \
    SERVICE_INSTAGRAM["user"], SERVICE_INSTAGRAM["location"], SERVICE_INSTAGRAM["info"], SERVICE_INSTAGRAM["task"], \
    SERVICE_INSTAGRAM["post"], SERVICE_INSTAGRAM["search"], SERVICE_INSTAGRAM["setting"]


def select_cookie_user(username):

    filter_raw = {
        "username" : username,
        "session": {"$exists": 1},
        "mobile_session": True,
        "status": "unavailable",
        "client_name": "admin_test",
        "channel": "instagram",
        # f"usage.dm": {"$lte": 10}
        "$or" : [
            {
                f"usage.dm.{datetime.now().strftime('%Y-%m-%d')}" : {"$lte": 10}
            },
            {
                f"usage.dm.{datetime.now().strftime('%Y-%m-%d')}": {"$exists": False}
            }
                ]
    }
    doc = ACCOUNT_COLLECTION.find_one(filter_raw)
    return doc
doc = select_cookie_user("ivujlamintaziva")
print(doc)
