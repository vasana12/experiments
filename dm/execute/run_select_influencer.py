from db import m_instagram
from dm.engine import completed_target_influencer
from instamanager import Bot
import logging
from dm.prepare import get_dm_source, get_influencer

FORMAT = '%(module)s.%(funcName)s - %(message)s - %(levelname)s - %(asctime)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)
if logger.hasHandlers():
    # Logger is already configured, remove all handlers
    logger.handlers = []
logger.setLevel(logging.INFO)

def get_influnecer_info_by_project(project_name,only_username=None, file_name = None):
    influencer_list = get_influencer.get_userinfo_by_project(project_name,only_username=only_username, file_name=file_name)
    return influencer_list


def get_influencer_info_by_username(username, collection_name):
    res = get_influencer.get_userinfo_by_username(username, collection_name)
    return res

def search_influencer_info(exclude_user_list=None):
    if not exclude_user_list:
        exclude_user_list = []
    skip = 0
    limit = 2000
    only_username = False

    collection_name = "user_checkpoint"
    search_hashtag = get_dm_source.get_source_hashtag("puzzle_pet.txt")
    # search_hashtag = "강아지키우고싶다"
    filename = f"puzzle_pet_{search_hashtag[0:10]}"


    search_filter = \
            {
                "user_followed_by": {
                    "$gte": 5500
                },
                # "avg_like":
                # {
                #     "$gte": 500
                # },
                "$text":
                    {
                        "$search": search_hashtag
                    },
                "username":{"$nin": exclude_user_list}
            }

    target_username_list = get_influencer.main(search_filter=search_filter,
                                               file_name=filename,
                                               skip=0,
                                               limit=limit,
                                               only_username=only_username,
                                               collection_name= collection_name)

    return target_username_list

username = get_influnecer_info_by_project(project_name="puzzle", only_username=True, file_name=None)
target_username_list = search_influencer_info(exclude_user_list=username)
print(len(target_username_list))
# username = get_influnecer_info_by_project(project_name="puzzle", file_name=None)