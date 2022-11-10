
from dm.engine.gpi import get_user_by_id_gpi
from db.model import *
from instagrapi.extractors import extract_media_v1
from gpi_auth import *

FORMAT = '%(module)s.%(funcName)s - %(message)s - %(levelname)s - %(asctime)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)
if logger.hasHandlers():
    # Logger is already configured, remove all handlers
    logger.handlers = []
logger.setLevel(logging.INFO)

host, port, proxy_username, proxy_password = "resi3.ipb.cloud", "9000", "AX7S3xZk5L9RF1So", "wifi;us;;;;"
proxy = f"http://{proxy_username}:{proxy_password}@{host}:{port}"

max_login_try_num = 2
max_messages_per_day = 100
max_group_size = 30

def infinite_login(client: Client, username, max_messages_per_day, client_name=None, session_id=None, proxy=None):
    while True:
        ##1. 사용할 계정 DB 에서 가져오기
        account_setting_info = select_user(username=None, client_name=client_name, max_messages_per_day=max_messages_per_day)

        if account_setting_info is None:
            logger.error("사용가능한 계정이 없습니다 infinite login 을 종료합니다.")
            raise AccountException

        ##2. 가져온 계정으로 로그인 시도. session 받아오기
        session_id = account_setting_info["session"]["sessionid"]
        if session_id:
            login_session = login_by_sessionid_v_gpi(client, session_id)
        else:
            login_session = login_v_gpi(client, account_setting_info["username"], account_setting_info["password"])


        ##2.1 가져온 계정으로 로그인이 성공한 경우 받아온 session을 return 해준다
        if login_session:
            account_setting_info.update(graph_session=client.sessionid)
            return account_setting_info

        ##2.2 가져온 계정으로 로그인이 실패한 경우 계정을 새로 가져온다.
        else:
            continue

def get_user_by_id(user_id):
    try:
        access_key = "nTYC9RbjpV8axJ3I9OnKI9Z4QVu7hzrE"
        headers = {"x-access-key": access_key}
        params = {"id": user_id}
        response = requests.get(url="https://api.lamadava.com/v1/user/by/id", params=params, headers=headers)
        json_data = json.loads(response.text)
    except Exception as e:
        logger.error(f"user_id:{user_id}/error:{e}")
        return None
    else:
        if json_data.get("pk") is None:
            logger.info(f"json_data:{json_data}")
            return None
        return json_data
def get_valid_user_ids(user_ids):
    valid_user_ids = []
    for user_id in user_ids:
        try:
            valid_user_id = get_user_by_id_gpi(user_id, proxy)
        except Exception as e:
            logger.warning(f"{e}//user_id-{user_id} is not valid_user_id,{e.__class__.__name__}")
            if e.__class__.__name__ == UserNotFound.__name__:
                ITEM_USER_COLLECTION.delete_many(filter={"$or": [{"pk": str(user_id)}, {"pk": int(user_id)}]})
                USER_CHECKPOINT.delete_many(filter={"$or": [{"userid": str(user_id)}, {"userid": int(user_id)}]})
            continue
        else:
            valid_user_ids.append(valid_user_id)
    # user_ids = list(filter(lambda x: get_user_by_id_lamadava(x), user_ids))
    # user_ids = list(filter(lambda x: x is not None, user_ids))
    return valid_user_ids

def get_posts(name, max_amount,tab_key, max_id):
    access_key = "nTYC9RbjpV8axJ3I9OnKI9Z4QVu7hzrE"
    headers = {"x-access-key": access_key}
    params = {"name": name, "max_amount": max_amount, "max_id": max_id}

    try:
        response = requests.get(url=f"https://api.lamadava.com/v1/hashtag/medias/{tab_key}/chunk", params=params, headers=headers)

        json_data = json.loads(response.text)
        medias = json_data[0]
        max_id = json_data[-1]

    except Exception as e:
        logger.error(f"name:{max_id}/error:{e.__class__.__name__}/{response.text}")
        return None
    else:
        return medias, max_id

def run(name, max_amount, tab_key):
    max_id = None
    while True:
        medias, max_id = get_posts(name=name, max_amount=max_amount,  tab_key=tab_key, max_id=max_id)


        if max_id is None:
            break
        for media in medias:
            yield media

def divide_user_infos_list(user_infos_list, group_size):
    # user_infos_list = list(map(lambda x: [x] if type(x) is not list else x, user_infos_list))
    total_user_infos_group = []
    group_size = min(max_group_size, group_size)

    total_user_infos_group_count = len(user_infos_list) / group_size
    total_user_infos_group_count = math.ceil(total_user_infos_group_count)

    logger.info(f"total_user_infos_group_count:{total_user_infos_group_count}")

    for i in range(0, total_user_infos_group_count):
        prev_page = group_size * i
        next_page = group_size * (i + 1)
        total_user_infos_group.append(user_infos_list[prev_page:next_page])
    return total_user_infos_group


if __name__ == "__main__":
    ##project 이름 과 제외할 프로젝트 이름
    name = "고구마"
    max_amount = 27
    tab_key = "top"
    for idx, media in enumerate(run(name=name, max_amount=max_amount, tab_key=tab_key)):
        extract_media_v1(media)

        # input()


