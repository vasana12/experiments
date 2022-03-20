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
limit = 3000
only_username = False
collection_name = "user_checkpoint"
search_hashtag = get_dm_source.get_source_hashtag("taewha.txt")
filename = f"taewha_{search_hashtag}"
# search_filter = \
#         {
#             "user_followed_by":
#                 {
#                     "$gte": 2000, "$lte":5000
#                 },
#             "avg_like":
#                 {
#                     "$gte": 50
#                 },
#             "$text":
#                 {
#                     "$search": search_hashtag
#                 }
#         }

search_filter = \
        {
            "user_followed_by":
                {
                    "$lte": 2000
                }
        }
target_username_list = get_influencer.main(search_filter=search_filter,
                                           file_name=filename,
                                           skip=0,
                                           limit=limit,
                                           only_username=only_username,
                                           collection_name= collection_name)
print(len(target_username_list))


