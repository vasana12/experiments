import json
from dm.prepare import get_dm_source
from dm.engine import user
from src.utils import get_project_root
from dm.model import Task
from dm.log import logger

project_dir = get_project_root()

def get_influencer_list_by_task(task:Task):
    ##1. project 이름 시작 기간 설정
    project = task.project.name
    project_start_date = task.project.start_date

    ##2. 파일이름 설정
    filename = f"{task.project.name}_{task.search_hashtag[0:15]}_{task.project.start_date}"

    ##3. 제외할 단어 유저이름, 프로젝트 설정
    exclude_word_list = task.exclude_hashtag
    exclude_word_list = list(map(lambda x: f"-{x}", exclude_word_list))
    exclude_word_list = " ".join(exclude_word_list)

    exclude_end_date = task.project.exclude_project_end_date
    exclude_start_date = task.project.exclude_project_start_date
    exclude_userid_list = user.find_completed_influencer(project_name=project, start_date=exclude_start_date, end_date=exclude_end_date)
    exclude_userid_list_int = list(map(lambda x: int(x), exclude_userid_list))
    exclude_userid_list = exclude_userid_list + exclude_userid_list_int
    exclude_username_list = []

    ##4. 몇개 가져올지 설정
    skip, limit = 0, task.size

    ##5. 검색 조건 필터
    user_followed_by_gte = task.user_followed_by_gte
    user_followed_by_lte = task.user_followed_by_lte
    avg_like_gte = task.avg_like_gte
    only_username = False
    spam_filter = task.spam_filter

    ##6. 타겟 해시태그 설정 해시태그 설정하지 않으면 프로젝트 이름이 default 로 들어감.
    search_hashtag = task.search_hashtag
    exclude_hashtag = task.exclude_hashtag
    # search_hashtag = get_dm_source.get_source_hashtag(f"{project}.txt")
    # search_hashtag = f"{search_hashtag}"

    search_filter = {"$text": {"$search": f"{search_hashtag} -{exclude_hashtag}", },
                     "user_followed_by": {"$gte": int(user_followed_by_gte), "$lte": int(user_followed_by_lte)},
                     "avg_like": {"$gte": int(avg_like_gte)},
                     "userid": {"$nin": exclude_userid_list},
                     "username": {"$nin": exclude_username_list},
                     # "$where": "this.user_followed_by > this.user_follow"
                     }
    user_infos_list = user.get_user(search_filter=search_filter, file_name=filename, skip=skip, limit=limit, only_username=only_username, collection_name=None)
    logger.info(search_filter)
    ##2. 유저 분할
    total_user_infos_group = user.divide_user_infos_list(user_infos_list, group_size=1)
    return total_user_infos_group

if __name__ == "__main__":
    # total_user_infos_group = get_influencer_list()
    task = get_dm_source.get_source(source_type="task", filename="hclass.py")
    task = json.loads(task)

    task = Task(**task)
    print(task)
