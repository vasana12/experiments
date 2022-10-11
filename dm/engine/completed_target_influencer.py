from db import m_instagram
import logging
import bson
from datetime import datetime, timedelta
from dm.prepare import get_influencer
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

PROJECT_DM, CLIENT_COLLECTION, HASHTAG_AND_USER_SEARCH, HASHTAG_AND_USER, PROJECT_COLLECTION, ITEM_HASHTAG_COLLECTION, ITEM_USER_COLLECTION, ITEM_LOCATION_COLLECTION, INFO_COLLECTION, TASK_COLLECTION, POST_COLLECTION, SEARCH_COLLECTION = \
    SERVICE_INSTAGRAM["project_dm"],SERVICE_INSTAGRAM["client"], SERVICE_INSTAGRAM["hashtag_and_user_search"], SERVICE_INSTAGRAM["hashtag_and_user"], \
    SERVICE_INSTAGRAM["project"], SERVICE_INSTAGRAM["hashtag"], SERVICE_INSTAGRAM["user"], SERVICE_INSTAGRAM["location"], \
    SERVICE_INSTAGRAM["info"], SERVICE_INSTAGRAM["task"], SERVICE_INSTAGRAM["post"], SERVICE_INSTAGRAM["search"]

def find_completed_influencer(project_name, start_date=None, end_date=None):
    start_date = datetime.now() if start_date is None else datetime.strptime(start_date, "%Y-%m-%d")
    end_date = datetime.now() if end_date is None else datetime.strptime(end_date, "%Y-%m-%d")
    filter_date = {"$lte": end_date, "$gte": start_date}

    field_entered = {"_id": 0, "influencer": 1}
    cursor = PROJECT_DM.find({"project": project_name, "start_date": filter_date}, field_entered)

    project_list = list(cursor)
    influencer_list = []
    for project in project_list:
        influencer_list.extend(project["influencer"])

    influencer_list = list(map(lambda x: str(x), influencer_list))
    return list(sorted(set(influencer_list),key=influencer_list.index))

# def find_project_user(project_name):
#     today = datetime.now() - timedelta(days=1)
#     filed_entered = {"_id":0, "influencer": 1}
#     project_doc = DM_COLLECTION.find_one({"project": project_name, "start_date": {"$lte": today}}, filed_entered)
#     return project_doc

def push_influencer_completed(project_name, start_date=None, influencer_completed=None):
    today = datetime.now().date()
    filter = {"project": project_name}
    if start_date is None:
        start_date = today
    else:
        start_date = datetime.strptime(start_date, "%Y-%m-%d")

    filter.update(start_date=start_date)

    ### when project already exist
    for influencer in influencer_completed:
        if PROJECT_DM.find_one_and_update(filter=filter, update={"$push": {"influencer": str(influencer)}}):
            logger.info(f"push :{influencer}")
            return

        ### when project not exist
        filter.update(influencer=[influencer], start_date=start_date)
        PROJECT_DM.insert_one(filter)
        logger.info(f" make new project {filter.get('project')}/ and insert :{influencer}")
        return


#
# def read_influencer_completed(project_name, start_date):
#
# # doc = find_project_list("taewha")
# # print(doc)
# project_name = "taewha"
# start_date = "2022-02-11"
#
# keyword_filter = "홍게 꽃게 농수산 먹방 요리 먹스타그램 새우 해산물 해물 조개 바다"
# serach_filter = search_filter = \
#         {
#             "user_followed_by":
#                 {
#                     "$gte": 2000
#                 },
#             "avg_like":
#                 {
#                     "$gte": 50
#                 },
#             "$text":
#                 {
#                     "$search": keyword_filter
#                 }
#         }
# influencer_list = get_influencer.main(search_filter=serach_filter, skip=0,limit=3000 , only_username = True)
# for influencer in influencer_list:
#     push_influencer_completed(project_name, start_date, influencer)
