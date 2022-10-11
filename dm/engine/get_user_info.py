import logging
from dm.engine.exceptions import LamadavaServerError
import requests
import json
from instamanager.api.manager_exceptions import NoUserIdException
from instagrapi.types import User
from instagrapi.utils import json_value
FORMAT = '%(module)s.%(funcName)s - %(message)s - %(levelname)s - %(asctime)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)
if logger.hasHandlers():
    # Logger is already configured, remove all handlers
    logger.handlers = []
logger.setLevel(logging.INFO)

def get_user_info_by_rapid_api(username):
    url = "https://instagram-scraper-2022.p.rapidapi.com/ig/web_profile_info/"

    querystring = {"user": username}

    headers = {
        "X-RapidAPI-Key": "49247615ccmshcd5a0d0e8ddb542p1ae266jsnb64d93ff541c",
        "X-RapidAPI-Host": "instagram-scraper-2022.p.rapidapi.com"
    }

    response = requests.request("GET", url, headers=headers, params=querystring)
    # params = {"username": username, "access_key": "nTYC9RbjpV8axJ3I9OnKI9Z4QVu7hzrE"}
    # response = requests.get(url="https://api.lamadava.com/a1/user", params=params)
    json_data = json.loads(response.text)
    return json_data


def get_user_info_by_name(username):
    max_try_num_get_user = 5
    try_num_get_user = 0
    while True:
        if try_num_get_user > max_try_num_get_user:
            logger.warning(f"LamadavaServerError")
            raise LamadavaServerError

        try:
            access_key = "nTYC9RbjpV8axJ3I9OnKI9Z4QVu7hzrE"
            headers = {"x-access-key": access_key}
            params = {"username": username}
            response = requests.get(url="https://api.lamadava.com/a1/user", params=params, headers=headers)
            data = json.loads(response.text)
            json_data = json_value(data, "graphql", "user")
        except Exception as e:
            logger.warning(f"username:{username}/error:{e}")
            try_num_get_user += 1
            continue
        else:
            exc_type = json_data.get("exc_type")
            if exc_type == "NoFreeAccounts":
                logger.warning(f"json_data:{json_data} retry-{try_num_get_user}/{max_try_num_get_user}")
                try_num_get_user += 1
                continue

            if exc_type == "InstagramServerError":
                logger.warning(f"json_data:{json_data} retry-{try_num_get_user}/{max_try_num_get_user}")
                try_num_get_user += 1
                continue

            if exc_type == "UserNotFound":
                logger.warning(f"존재하지 않는 userid")
                raise NoUserIdException

            # if json_data.get("pk") is None:
            #     logger.error(f"username:{username}/{json_data}")
            #     try_num_get_user += 1
            #     continue

            ###response type check(User Validation)
            else:
            #     try:
            #         User(**json_data)
            #     except Exception as e:
            #         logger.warning(f"json_data:{json_data}/{e} retry-{try_num_get_user}/{max_try_num_get_user}")
            #         try_num_get_user += 1
            #         continue
                return json_data


def get_user_info_by_id_lamadava(user_id):
    max_try_num_get_user = 5
    try_num_get_user = 0
    while True:
        if try_num_get_user > max_try_num_get_user:
            logger.warning(f"LamadavaServerError")
            raise LamadavaServerError

        try:
            access_key = "nTYC9RbjpV8axJ3I9OnKI9Z4QVu7hzrE"
            headers = {"x-access-key": access_key}
            params = {"id": user_id}
            response = requests.get(url="https://api.lamadava.com/v1/user/by/id", params=params, headers=headers)
            json_data = json.loads(response.text)
        except Exception as e:
            logger.warning(f"user_id:{user_id}/error:{e}")
            try_num_get_user += 1
            continue
        else:
            exc_type = json_data.get("exc_type")
            if exc_type == "NoFreeAccounts":
                logger.warning(f"json_data:{json_data} retry-{try_num_get_user}/{max_try_num_get_user}")
                try_num_get_user += 1
                continue

            if exc_type == "InstagramServerError":
                logger.warning(f"json_data:{json_data} retry-{try_num_get_user}/{max_try_num_get_user}")
                try_num_get_user += 1
                continue

            if exc_type == "UserNotFound":
                logger.warning(f"존재하지 않는 userid")
                raise NoUserIdException

            if json_data.get("pk") is None:
                logger.error(f"user_id:{user_id}/{json_data}")
                try_num_get_user += 1
                continue

            ###response type check(User Validation)
            else:
                try:
                    User(**json_data)
                except Exception as e:
                    logger.warning(f"json_data:{json_data}/{e} retry-{try_num_get_user}/{max_try_num_get_user}")
                    try_num_get_user += 1
                    continue

            return json_data

# userinfo = get_user_info_by_rapid_api("faker")
# print(userinfo)
for i in range(0,10):
    userinfo = get_user_info_by_name(username="faker")
    print(userinfo)
