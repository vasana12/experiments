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



skip = 0
limit = 500
only_username = False

search_hashtag = "공구 공동구매 협찬 공구오픈 공구예정 공구알림 효소"
filename = f"brandot_{search_hashtag}"
search_filter = \
        {
            "user_followed_by":
                {
                    "$gte": 6000
                },
            "avg_like":
                {
                    "$gte": 300
                },
            "avg_comment":
                {
                    "$gte": 20
                },
            "$text":
                {
                    "$search": search_hashtag
                }
        }
target_username_list = get_influencer.main(search_filter=search_filter, file_name=filename, skip=0, limit=limit, only_username=only_username, collection_name="user_checkpoint")
print(target_username_list)
print(len(target_username_list))


