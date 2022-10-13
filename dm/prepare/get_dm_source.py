from datetime import datetime
from datetime import timedelta
import logging
from db import m_instagram
from pathlib import Path
insta_db = m_instagram.InstaDB(db_name="account")
account_collection = insta_db.account_collection

FORMAT = 'INSTAGRAM_TARGETING_BOTs %(asctime)s - %(levelname)s - %(name)s - %(module)s.%(funcName)s - %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

JIN_INSTAGRAM = m_instagram.InstaDB(db_name="instagram_analysis").db
JIN_ACCOUNT = JIN_INSTAGRAM["account"]

SERVICE_INSTAGRAM = m_instagram.InstaDB(db_name="service_instagram").db
INSTA_ACCOUNT_OBJ = m_instagram.InstaAccount(client_name="admin", channel_name="instagram").db
ACCOUNT_COLLECTION = INSTA_ACCOUNT_OBJ['account']
BAND_ACCOUNT, HASHTAG_AND_USER, PROJECT_COLLECTION, ITEM_HASHTAG_COLLECTION, ITEM_USER_COLLECTION, ITEM_LOCATION_COLLECTION, INFO_COLLECTION, TASK_COLLECTION, POST_COLLECTION, SEARCH_COLLECTION = \
    SERVICE_INSTAGRAM["account_instagram"], SERVICE_INSTAGRAM["hashtag_and_user"], SERVICE_INSTAGRAM["project"], SERVICE_INSTAGRAM["hashtag"], \
    SERVICE_INSTAGRAM["user"], SERVICE_INSTAGRAM["location"], SERVICE_INSTAGRAM["info"], SERVICE_INSTAGRAM["task"], \
    SERVICE_INSTAGRAM["post"], SERVICE_INSTAGRAM["search"]


def get_source(source_type, filename):
    """source_type : ['hashtag', 'message']"""
    project_dir = Path.cwd().parent
    filepath = project_dir.joinpath("source", source_type, filename)
    return filepath.read_text(encoding="utf-8")


def get_source_message(filename):
    """ get source -  message from local directory"""
    return get_source("message", filename)


def get_source_hashtag(filename):
    """ get soruce - hashtag from local directory"""
    return get_source("hashtag",filename)