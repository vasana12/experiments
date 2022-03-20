import logging
import uuid
import logging
from pathlib import Path
import bson
import pandas as pd
from db import m_instagram
from dm.prepare import get_dm_source

FORMAT = '%(module)s.%(funcName)s - %(message)s - %(levelname)s - %(asctime)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)
if logger.hasHandlers():
    # Logger is already configured, remove all handlers
    logger.handlers = []
logger.setLevel(logging.INFO)
SERVICE_INSTAGRAM = m_instagram.InstaDB(db_name="service_instagram").db
ACCOUNT_COLLECTION = m_instagram.InstaDB(db_name="account").account_collection
INSTA_ACCOUNT_OBJ = m_instagram.InstaAccount(channel_name="instagram")
INSTA_ACCOUNT_OBJ.client_name = "admin_test"
USER_CHECKPOINT, CLIENT_COLLECTION, HASHTAG_AND_USER_SEARCH, HASHTAG_AND_USER, PROJECT_COLLECTION, ITEM_HASHTAG_COLLECTION, ITEM_USER_COLLECTION, ITEM_LOCATION_COLLECTION, INFO_COLLECTION, TASK_COLLECTION, POST_COLLECTION, SEARCH_COLLECTION = \
    SERVICE_INSTAGRAM["user_checkpoint"],SERVICE_INSTAGRAM["client"], SERVICE_INSTAGRAM["hashtag_and_user_search"], SERVICE_INSTAGRAM["hashtag_and_user"], \
    SERVICE_INSTAGRAM["project"], SERVICE_INSTAGRAM["hashtag"], SERVICE_INSTAGRAM["user"], SERVICE_INSTAGRAM["location"], \
    SERVICE_INSTAGRAM["info"], SERVICE_INSTAGRAM["task"], SERVICE_INSTAGRAM["post"], SERVICE_INSTAGRAM["search"]
HASHTAG_AND_USER_SEARCH.with_options(codec_options = bson.CodecOptions(unicode_decode_error_handler="ignore"))

def save_file(data:list,file_name =None):
    project_path = Path.cwd().parent
    result_path = project_path.joinpath("result","target_influencer_list")
    df = pd.DataFrame(data)
    file_name = uuid.uuid4() if file_name is None else file_name
    df.to_excel(f"{result_path}/{file_name}.xlsx")

def get_influencers(search_filter,influencer_skip=0 ,influencer_limit=0, only_username= False,collection_name=None):
    collection_lookup = {"hashtag_and_user_search" : HASHTAG_AND_USER_SEARCH, "user_checkpoint":USER_CHECKPOINT}
    selected_collection = collection_lookup.get(collection_name)
    if selected_collection is None:
        logger.error(f"you choose wrong collection collection : you can choose {','.join(collection_lookup.keys())} ")
        return
    field_exclude = {"contact_phone":False, "contact_email":False,"_id": False,"recent_posts":False, "search": False,"thumbnail_url": False,"hashtag": False,"likes": False,"comments": False,"crawled_date_time":False,"analyzed_date_time":False,"dateField":False,"avg_point":False,"activity_category":False,"brand":False,"expected_pay_photo":False,"expected_pay_product":False,"sex":False,"sns_facebook":False,"sns_naver":False,"sns_tiktok":False,"sns_youtube":False,"userid":False,"top_posts":False,"top_users":False}
    only_username_field_exclude = {"_id": 0,"username":1}
    field_exclude = only_username_field_exclude if only_username else field_exclude
    cursor = selected_collection.find(search_filter,field_exclude).skip(influencer_skip).limit(influencer_limit)
    influencer_list = list(cursor)

    if only_username :
        influencer_list = list(map(lambda x: x["username"], influencer_list))
        return influencer_list
    return influencer_list

def main(search_filter=None, file_name=None, skip=None, limit=None, only_username=None, collection_name="hashtag_and_user_search"):
    influencer_data_list = get_influencers(search_filter=search_filter, influencer_skip=skip, influencer_limit=limit, only_username=only_username, collection_name = collection_name)
    if file_name:
        save_file(influencer_data_list, f"{file_name}_인플루언서_{limit}")
    return influencer_data_list
