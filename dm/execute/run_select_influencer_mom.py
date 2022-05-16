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
limit = 20000
only_username = False
collection_name = "user_checkpoint"
search_hashtag = get_dm_source.get_source_hashtag("jusik.txt")
print(search_hashtag)
filename = f"jusik_{search_hashtag}"

search_filter = \
        {
            "user_followed_by":
                {
                    "$lte": 5000,
                },
            "$text":
                {
                    "$search": search_hashtag
                }
        }


target_username_list = get_influencer.main(search_filter=search_filter,
                                           file_name=filename,
                                           skip=0,
                                           limit=limit,
                                           only_username=only_username,
                                           collection_name= collection_name)
print(len(target_username_list))


