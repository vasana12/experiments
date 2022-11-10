from pathlib import Path
from datetime import datetime
import math
from db.model import *
from dm.log import logger
from dm import config
import pandas as pd
import uuid
import pymongo

def save_file(data:list, file_name):
    project_path = Path.cwd().parent
    result_path = project_path.joinpath("result", "target_influencer_list")
    df = pd.DataFrame(data)
    file_name = uuid.uuid4() if file_name is None else file_name
    df.to_excel(f"{result_path}/{file_name}.xlsx")

def user_split(username_list):
    k = username_list.split("\n")
    return k


def get_user(search_filter=None, file_name=None, skip=None, limit=None, only_username=None, collection_name=None, spam_filter=None):
    field_exclude = {"profile_url": False, "collection_from": False, "status": False, "contact_phone": False,
                     "contact_email": False, "_id": False, "recent_posts": False, "search": False,
                     "thumbnail_url": False, "hashtag": False, "likes": False, "comments": False,
                     "crawled_date_time": False, "analyzed_date_time": False, "dateField": False, "avg_point": False,
                     "activity_category": False, "brand": False, "expected_pay_photo": False,
                     "expected_pay_product": False, "sex": False, "sns_facebook": False, "sns_naver": False,
                     "sns_tiktok": False, "sns_youtube": False, "top_posts": False, "top_users": False}

    only_username_field_exclude = {"_id": 0, "username": 1}
    field_exclude = only_username_field_exclude if only_username else field_exclude

    if collection_name == "user_checkpoint":
        search_filter.update(collection_from={"$exists": False})

    cursor = USER_CHECKPOINT.find(search_filter, field_exclude).skip(skip).limit(limit).sort([('analyzed_date_time', pymongo.DESCENDING)])

    influencer_data_list = list(cursor)
    save_data_list = list(map(lambda x:
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

    if spam_filter:
        influencer_data_list = get_user_by_spam_filter(influencer_data_list)

    if file_name:
        save_file(save_data_list, f"{file_name}_인플루언서_{limit}")
    return_data_list = list(map(lambda x:
                                {
                                    "username": x["username"],
                                    "userid": x["userid"]
                                },
                                influencer_data_list))
    return return_data_list

def get_user_by_spam_filter(influencer_data_list):
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
            filtered_influencer_data_list.append(influencer)
    return filtered_influencer_data_list

def divide_user_infos_list(user_infos_list, group_size):
    # user_infos_list = list(map(lambda x: [x] if type(x) is not list else x, user_infos_list))
    total_user_infos_group = []
    group_size = min(config.max_group_size, group_size)

    total_user_infos_group_count = len(user_infos_list) / group_size
    total_user_infos_group_count = math.ceil(total_user_infos_group_count)

    logger.info(f"total_user_infos_group_count:{total_user_infos_group_count}")

    for i in range(0, total_user_infos_group_count):
        prev_page = group_size * i
        next_page = group_size * (i + 1)
        total_user_infos_group.append(user_infos_list[prev_page:next_page])
    return total_user_infos_group

def find_completed_influencer(project_name, start_date=None, end_date=None):
    start_date = datetime.now() if start_date is None else datetime.strptime(start_date, "%Y-%m-%d")
    end_date = datetime.now() if end_date is None else datetime.strptime(end_date, "%Y-%m-%d")
    filter_date = {"$lte": end_date, "$gte": start_date}

    field_entered = {"_id": 0, "influencer": 1}
    cursor = PROJECT_DM.find({"project": project_name, "start_date": filter_date}, field_entered)
    print(filter_date)
    project_list = list(cursor)
    influencer_list = []
    for project in project_list:
        influencer_list.extend(project["influencer"])

    influencer_list = list(map(lambda x: str(x), influencer_list))
    return list(sorted(set(influencer_list),key=influencer_list.index))

def push_influencer_completed(project_name, start_date=None, influencer_completed=None):
    today = datetime.now().date()
    filter = {"project": project_name}
    if start_date is None:
        start_date = today
    else:
        start_date = datetime.strptime(start_date, "%Y-%m-%d")

    filter.update(start_date=start_date)

    ### when project already exist
    if influencer_completed is not list:
        influencer_completed = [influencer_completed]

    for influencer in influencer_completed:
        if PROJECT_DM.find_one_and_update(filter=filter, update={"$push": {"influencer": str(influencer)}}):
            logger.info(f"push :{influencer}")
            return

        ### when project not exist
        filter.update(influencer=[influencer], start_date=start_date)
        PROJECT_DM.insert_one(filter)
        logger.info(f" make new project {filter.get('project')}/ and insert :{influencer}")
        return