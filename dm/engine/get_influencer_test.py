import json
import math
import sys
import requests
import time
from instagrapi import Client
from instagrapi.types import User
import logging
from instagrapi.types import DirectMessage
from db import m_instagram
from dm.engine import completed_target_influencer
from dm.engine.exceptions import *
from dm.execute.run_select_influencer import get_influnecer_info_by_project, search_influencer_info, get_influnecer_user_id_by_project
from dm.prepare import get_dm_source, get_influencer

FORMAT = '%(module)s.%(funcName)s - %(message)s - %(levelname)s - %(asctime)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)
if logger.hasHandlers():
    # Logger is already configured, remove all handlers
    logger.handlers = []
logger.setLevel(logging.INFO)

host, port, proxy_username, proxy_password = "resi3.ipb.cloud", "9000", "MrIlCvzYImHc0I3t", "wifi;us;;;;"
proxy = f"http://{proxy_username}:{proxy_password}@{host}:{port}"

db_conn = m_instagram.InstaDB().conn
INSTA_ACCOUNT_OBJ = m_instagram.InstaAccount(channel_name="instagram")
INSTA_ACCOUNT_OBJ.client_name = "admin_test"
max_messages_per_day = 200
max_group_size = 30


def get_user(skip, limit, search_filter, filename, exclude_word):
    target_username_list = search_influencer_info(skip=skip, limit=limit, search_filter=search_filter, only_username=False, filename=filename)
    if exclude_word is not None:
        target_username_list = list(filter(lambda x: exclude_word not in x["username"], target_username_list))
    target_username_list = list(map(lambda x: {"userid": int(x["userid"]) if "userid" in x.keys() else None,
                                               "username": x["username"] if "username" in x.keys() else None},
                                    target_username_list))

    target_username_list = list(filter(lambda x: x is not None, target_username_list))
    return target_username_list


if __name__ == "__main__":
    ##project 이름 과 제외할 프로젝트 이름
    project = "butterfly"
    start_date = "2022-10-08"

    ##제외할 단어 유저이름, 프로젝트 설정
    exclude_word = None

    # exclude_word =
    exclude_end_date = "2022-10-07"
    exclude_start_date = "2022-10-07"
    exclude_userid_list = completed_target_influencer.find_completed_influencer(project_name=project,
                                                                                start_date=exclude_start_date,
                                                                                end_date=exclude_end_date)
    exclude_userid_list_int = list(map(lambda x: int(x), exclude_userid_list))
    exclude_userid_list = exclude_userid_list + exclude_userid_list_int

    ##타겟 해시태그 설정 해시태그 설정하지 않으면 프로젝트 이름이 default 로 들어감.
    # search_hashtag = "관리하는여자 헬스녀 여자헬스 폴댄스 헬스하는여자 러닝하는여자"
    # search_hashtag = "촬영문의 여자모델 여성모델 촬영 여자메이크업"
    # search_hashtag = "힙업운동 애플힙 여자엉덩이 여자바디프로필 힙업 비키니선 엉짱 엉짱녀 개미허리 태닝하는여자 태닝녀 피치힙 힙운동 몸매스타그램 여자바프 여자스쿼트 레깅스"

    # search_hashtag = "모노키니 인피니티풀 풀웨어 비치웨어 섹시비키니 란제리 여자수영복 호텔수영장 휴가룩 바캉스룩 비치"
    include_userid_list = exclude_userid_list

    # search_hashtag = "필라테스강사 필라테스 요가강사 요가"
    search_hashtag = get_dm_source.get_source_hashtag(f"{project}.txt")

    ##파일이름
    filename = f"a_{project}_{search_hashtag[0:20]}_{start_date}"
    # text = get_dm_source.get_source_message(f"{project}.txt")
    ##몇개 가져올지
    skip, limit = 0, 3000
    """
    rang_mommy, 95.yeon, cola_b.mom, ham_hyeonju, ZZANGYOOOU, jy_312n, sortie2017, boon._.ddo, nna_young_
    """
    ##서치 필터플
    user_followed_by_gte = 3000
    user_followed_by_lte = 30000
    # avg_like_gte = 100
    # avg_comment = 10
    # user_follow_by_gte = 0
    # user_follow_by_lte = 15000
    search_filter = {"$text":
                         {
                             "$search": search_hashtag
                         },
                     "user_followed_by":
                         {
                             "$gte": int(user_followed_by_gte), "$lte": int(user_followed_by_lte)
                         },
                    # "user_follow":
                    #     {
                    #         "$gte": int(user_follow_by_gte), "$lte": int(user_follow_by_lte)
                    #     },
                     # "avg_like":
                     #     {
                     #         "$gte": int(avg_like_gte)
                     #     },
                    # "avg_comment":
                    #     {
                    #         "$gte": int(avg_comment)
                    #     },
        # "userid": {"$nin": exclude_userid_list},
        "userid": {"$in": include_userid_list}
    }

    user_infos_list = get_user(skip=skip, limit=limit, search_filter=search_filter, filename=filename, exclude_word=exclude_word)
    user_infos_list = list(map(lambda x: x["userid"], user_infos_list))
    print(len(user_infos_list))
    ##1. 유저 리스트 추출



