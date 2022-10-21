import logging
import uuid
import logging
from pathlib import Path
import bson
import pandas as pd
import pymongo

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

USER_CHECKPOINT, CLIENT_COLLECTION, HASHTAG_AND_USER_SEARCH, PROJECT_DM_COLLECTION, ITEM_HASHTAG_COLLECTION, ITEM_USER_COLLECTION, ITEM_LOCATION_COLLECTION, INFO_COLLECTION, TASK_COLLECTION, POST_COLLECTION, SEARCH_COLLECTION = \
    SERVICE_INSTAGRAM["user_checkpoint"],SERVICE_INSTAGRAM["client"], SERVICE_INSTAGRAM["hashtag_and_user_search"], SERVICE_INSTAGRAM["project_dm"], \
    SERVICE_INSTAGRAM["hashtag"], SERVICE_INSTAGRAM["user"], SERVICE_INSTAGRAM["location"], \
    SERVICE_INSTAGRAM["info"], SERVICE_INSTAGRAM["task"], SERVICE_INSTAGRAM["post"], SERVICE_INSTAGRAM["search"]

HASHTAG_AND_USER_SEARCH.with_options(codec_options = bson.CodecOptions(unicode_decode_error_handler="ignore"))

def save_file(data:list,file_name =None):
    project_path = Path.cwd().parent
    result_path = project_path.joinpath("result","target_influencer_list")
    df = pd.DataFrame(data)
    file_name = uuid.uuid4() if file_name is None else file_name
    df.to_excel(f"{result_path}/{file_name}.xlsx")

def get_userinfo_by_project(project_name, only_username = None, file_name = None):
    projects = list(PROJECT_DM_COLLECTION.find({"project": {"$regex": project_name}}))
    influencer_list = []
    for project_info in projects:
        influencer_list.extend(project_info["influencer"])
    influencer_list = list(set(influencer_list))
    if only_username:
        influencer_data_list = list(USER_CHECKPOINT.find({"username": {"$in": influencer_list}}))
        influencer_data_list = list(map(lambda x: x["username"],influencer_data_list))
    else:
        influencer_data_list = list(USER_CHECKPOINT.find({"username":{"$in":influencer_list}}))
    if file_name:
        save_file(influencer_data_list, f"{file_name}_인플루언서")
    return influencer_data_list

def get_userid_by_project(project_name, ex_project_start_date=None, only_userid = None, file_name = None):
    if ex_project_start_date is None:
        projects = list(PROJECT_DM_COLLECTION.find({"project": {"$regex": project_name}}))
    else:
        projects = list(PROJECT_DM_COLLECTION.find({"project": {"$regex": project_name, "$lte":ex_project_start_date}}))

    influencer_list = []
    for project_info in projects:
        influencer_list.extend(project_info["influencer"])
    print(f"influencer_list:{influencer_list}")
    influencer_list = list(set(influencer_list))
    if only_userid:
        influencer_data_list = list(USER_CHECKPOINT.find({"userid": {"$in": influencer_list}}))
        influencer_data_list = list(map(lambda x: x["userid"],influencer_data_list))
    else:
        influencer_data_list = list(USER_CHECKPOINT.find({"userid":{"$in":influencer_list}}))
    if file_name:
        save_file(influencer_data_list, f"{file_name}_인플루언서")
    return influencer_data_list

def get_influencers(search_filter,influencer_skip=0 ,influencer_limit=0, only_username= False,collection_name=None):

    field_exclude = {"profile_url": False, "collection_from":False, "status":False, "contact_phone":False, "contact_email":False, "_id": False, "recent_posts": False, "search": False, "thumbnail_url": False, "hashtag": False, "likes": False, "comments": False, "crawled_date_time":False,"analyzed_date_time":False,"dateField":False,"avg_point":False,"activity_category":False,"brand":False,"expected_pay_photo":False,"expected_pay_product":False,"sex":False,"sns_facebook":False,"sns_naver":False,"sns_tiktok":False,"sns_youtube":False, "top_posts":False,"top_users":False}

    only_username_field_exclude = {"_id": 0, "username": 1}
    field_exclude = only_username_field_exclude if only_username else field_exclude

    if collection_name == "user_checkpoint":
        search_filter.update(collection_from={"$exists":False})
    cursor = USER_CHECKPOINT.find(search_filter, field_exclude).skip(influencer_skip).limit(influencer_limit).sort([('analyzed_date_time', pymongo.DESCENDING)])

    influencer_list = list(cursor)

    if only_username :
        influencer_list = list(map(lambda x: x["username"], influencer_list))
        return influencer_list
    return influencer_list

def get_userinfo_by_username(username, collection_name):
    collection_lookup = {"hashtag_and_user_search": HASHTAG_AND_USER_SEARCH, "user_checkpoint": USER_CHECKPOINT}
    selected_collection = collection_lookup.get(collection_name)
    if selected_collection is None:
        logger.error(f"you choose wrong collection collection : you can choose {','.join(collection_lookup.keys())} ")
        return
    field_exclude = {"contact_phone": False, "contact_email": False, "_id": False, "recent_posts": False,
                     "search": False, "thumbnail_url": False, "hashtag": False, "likes": False, "comments": False,
                     "crawled_date_time": False, "analyzed_date_time": False, "dateField": False, "avg_point": False,
                     "activity_category": False, "brand": False, "expected_pay_photo": False,
                     "expected_pay_product": False, "sex": False, "sns_facebook": False, "sns_naver": False,
                     "sns_tiktok": False, "sns_youtube": False, "userid": False, "top_posts": False, "top_users": False, "status":False}
    return selected_collection.find_one({"username":username}, field_exclude)

def main(search_filter=None, file_name=None, skip=None, limit=None, only_username=None, collection_name=None):
    influencer_data_list = get_influencers(search_filter=search_filter, influencer_skip=skip, influencer_limit=limit, only_username=only_username, collection_name = collection_name)

    influencer_data_list = list(map(lambda x:
                                    {
                                        "username": x["username"],
                                        "mediacount": x["mediacount"],
                                        "userid": x["userid"],
                                        "user_biography": x["user_biography"],
                                        "user_external_url": x["user_external_url"],
                                        "user_follow": x["user_follow"],
                                        "user_followed_by": x["user_followed_by"],
                                        "search_content": x["search_content"]
                                              },
                                    influencer_data_list))
    filtered_influencer_data_list = []
    for influencer in influencer_data_list:
        user_followed_by = influencer["user_followed_by"]
        user_follow = influencer["user_follow"]

        # #필터2
        # if user_follow*10 > user_followed_by > user_follow*2:
        #     print(user_follow, user_followed_by)
        #     filtered_influencer_data_list.append(influencer)
        #
        # 필터1
        if user_followed_by>user_follow:
            # print(user_follow, user_followed_by)
            filtered_influencer_data_list.append(influencer)
    filtered_influencer_data_list = influencer_data_list
    if file_name:
        save_file(filtered_influencer_data_list, f"{file_name}_인플루언서_{limit}")
    return influencer_data_list
