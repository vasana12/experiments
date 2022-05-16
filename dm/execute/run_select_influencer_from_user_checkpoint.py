import logging
from dm.prepare import get_influencer

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

search_hashtag = "메이크업 립스틱 붓기차 여름코디 안다르 립스틱 틴트 붓기차 디톡스 오운완 젝시믹스 룰루레몬 여자데일리룩 운동하는여자 요가 필라테스 레깅스 여름코디 단발 식이요법 "
filename = f"puzzle_{search_hashtag}"
search_filter = \
        {
            "user_followed_by":
                {
                    "$gte": 10000
                },
            "$text":
                {
                    "$search": search_hashtag
                }
        }
target_username_list = get_influencer.main(search_filter=search_filter, file_name=filename, skip=0, limit=limit, only_username=only_username, collection_name="user_checkpoint")

print(len(target_username_list))


