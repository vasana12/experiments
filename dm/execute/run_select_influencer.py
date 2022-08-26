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


def search_influencer_info(search_hashtag, skip, limit, only_username, filename, exclude_user_list=None):
    if not exclude_user_list:
        exclude_user_list = []
    collection_name = None
    # search_hashtag = get_dm_source.get_source_hashtag("gen.txt")
    print(search_hashtag)

    search_filter = \
            {
                "$text":
                    {
                        "$search": search_hashtag,
                    },
                "user_followed_by": {"$gte": 20000},
                # "avg_like": {"$gte": 30},
                "username": {"$nin": exclude_user_list}
            }

    target_username_list = get_influencer.main(search_filter=search_filter,
                                               file_name=filename,
                                               skip=skip,
                                               limit=limit,
                                               only_username=only_username,
                                               collection_name= collection_name)

    return target_username_list

if __name__ == "__main__":
    filename = "퍼즐_페이퍼"
    # exclude_username_list = get_influnecer_info_by_project(project_name="rounded", only_username=True)
    exclude_username_list = []
    exclude_word = None
    search_hashtag = get_dm_source.get_source_hashtag("puzzle_paper.txt")
    # search_hashtag = "제주도 제테크 투자 골프스타그램 스크린골프 골프웨어 골프중독 라운딩 라운딩패션 골프화 골프레슨 스포츠 공구 공구진행 협찬 베이비 2살 3살 10개월"
    limit = 2000
    skip = 0
    only_username = False

    target_username_list = search_influencer_info(search_hashtag=search_hashtag, limit=limit, skip=skip,only_username=only_username, filename=filename, exclude_user_list=exclude_username_list)
    target_username_list = list(filter(lambda x: exclude_word not in x, target_username_list))
    target_username_list = list(map(lambda x: {"userid":int(x["userid"]) if "userid" in x.keys() else None, "username": x["username"] if "username" in x.keys() else None}, target_username_list))
    target_username_list = list(filter(lambda x: x is not None, target_username_list))
    print(target_username_list)
    print(len(target_username_list))