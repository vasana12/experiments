import json
import requests
import time
from dm.engine.exceptions import RapidApiError, LamadavaServerError, NoUserIdException
from instagrapi import Client
from dm.log import logger
from db.model import *
from db import m_instagram
from dm.prepare import get_dm_source
from instagrapi.exceptions import UserNotFound, ClientError, HashtagNotFound
from instagrapi.types import User

access_key = "nTYC9RbjpV8axJ3I9OnKI9Z4QVu7hzrE"
headers = {"x-access-key": access_key}

db_conn = m_instagram.InstaDB().conn
INSTA_ACCOUNT_OBJ = m_instagram.InstaAccount(channel_name="instagram")
INSTA_ACCOUNT_OBJ.client_name = "admin_test"


def get_user_id_by_db(username):
    doc = USER_CHECKPOINT.find_one({"username": username})
    return doc["userid"]

def get_user_by_username_lamadava(username):
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
            response = requests.get(url="https://api.lamadava.com/v1/user/by/username", params=params, headers=headers)
            json_data = json.loads(response.text)
        except Exception as e:
            logger.warning(f"username:{username}/error:{e}")
            try_num_get_user += 1
            continue
        else:
            exc_type = json_data.get("exc_type")
            if exc_type == "NoFreeAccounts":
                try_num_get_user += 1
                logger.warning(f"json_data:{json_data} retry-{try_num_get_user}/{max_try_num_get_user}")
                continue

            if exc_type == "InstagramServerError":
                try_num_get_user += 1
                logger.warning(f"json_data:{json_data} retry-{try_num_get_user}/{max_try_num_get_user}")
                continue

            if exc_type == "UserNotFound":
                logger.warning(f"존재하지 않는 user")
                raise NoUserIdException

            if json_data.get("pk") is None:
                logger.error(f"username:{username}/{json_data}")
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
            return json_data["pk"]

def get_user_by_id_lamadava(user_id):
    max_try_num_get_user = 10
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
                try_num_get_user += 1
                logger.warning(f"json_data:{json_data} retry-{try_num_get_user}/{max_try_num_get_user}")
                continue

            if exc_type == "InstagramServerError":
                try_num_get_user += 1
                logger.warning(f"json_data:{json_data} retry-{try_num_get_user}/{max_try_num_get_user}")
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

def get_user_id_by_username_rapid_api(username):
    max_try_num_get_user = 5
    try_num_get_user = 0

    while True:
        if try_num_get_user > max_try_num_get_user:
            logger.warning(f"RapidApiError")
            raise RapidApiError
        try:

            url = "https://instagram-scraper-2022.p.rapidapi.com/ig/web_profile_info/"

            querystring = {"user": username}

            headers = {
                "X-RapidAPI-Key": "49247615ccmshcd5a0d0e8ddb542p1ae266jsnb64d93ff541c",
                "X-RapidAPI-Host": "instagram-scraper-2022.p.rapidapi.com"
            }
            response = requests.request("GET", url, headers=headers, params=querystring)
            # params = {"username": username, "access_key": "nTYC9RbjpV8axJ3I9OnKI9Z4QVu7hzrE"}
            # response = requests.get(url="https://api.lamadava.com/a1/user", params=params)
            json_data= json.loads(response.text)
        except Exception as e:
            time.sleep(20)
            logger.warning(f"user_id:{username}/error:{e}")
            try_num_get_user += 1
            continue
        else:
            if json_data.get("data") is None:
                logger.warning(f"username:{username}/error:{json_data}")
                if json_data.get("message") is not None and "Page not found":
                    raise UserNotFound
                try_num_get_user += 1
                continue
            else:
                id = json_data["data"]["user"]["id"]
                return id

def get_user_profile_by_id_gpi(userid, proxy=None):
    host, port, proxy_username, proxy_password = "residential.ipb.cloud", "7777", "customer-cbzh21909501-asn-20057-sessid-BIRQ-sesstime-1", "Q31n7pniF"
    proxy = f"http://{proxy_username}:{proxy_password}@{host}:{port}"
    # if proxy
    client = Client(proxy=proxy)

    try:
        response = client.user_short_gql(user_id=userid)
    except Exception as e:
        logger.debug("short 실패")
        if e.__class__.__name__ == UserNotFound.__name__:
            raise e
        elif e.__class__.__name__ == ClientError.__name__:
            response = get_user_by_id_lamadava(userid)
            return response.get("profile_pic_url")
    else:
        logger.debug("short 성공")
        return response.profile_pic_url

def get_user_by_id_gpi(userid):
    client = Client()
    try:
        response = client.user_short_gql(user_id=userid)
        print(response)
    except Exception as e:
        if e.__class__.__name__ == UserNotFound.__name__:
            raise e
        elif e.__class__.__name__ == ClientError.__name__:
            response = get_user_by_id_lamadava(userid)
            userid = response.get("pk")
    return int(userid)



def get_user_by_id(user_id):
    params = {"id": user_id}
    response = requests.get(url="https://api.lamadava.com/v1/user/by/id", params=params, headers=headers)
    json_data = json.loads(response.text)
    return json_data


def send_messages(session_id, user_ids, text, max_messages_per_day):
    access_key = "nTYC9RbjpV8axJ3I9OnKI9Z4QVu7hzrE"
    headers = {"x-access-key": access_key}
    user_ids = list(map(lambda x: str(x), user_ids))
    user_ids = list(set(user_ids))


    for idx, user_id in enumerate(user_ids):
        data = {"sessionid": session_id, "user_ids": [user_id], "text": f"{text}", }
        url = "https://api.lamadava.com/s1/direct/send"
        response = requests.post(url=url, data=data, headers=headers)
        print(idx, user_id, response.text)
        time.sleep(10)

        if idx == max_messages_per_day:
            broken_items = user_ids[user_ids.index(user_id):]
            return broken_items

def get_hashtag_by_name_lamadava(name):
    max_try_num_get_user = 5
    try_num_get_user = 0

    while True:
        if try_num_get_user > max_try_num_get_user:
            logger.warning(f"LamadavaServerError")
            raise LamadavaServerError

        try:
            access_key = "nTYC9RbjpV8axJ3I9OnKI9Z4QVu7hzrE"
            headers = {"x-access-key": access_key}
            params = {"name": name}
            response = requests.get(url="https://api.lamadava.com/a1/hashtag", params=params, headers=headers)
            json_data = json.loads(response.text)
        except Exception as e:
            logger.warning(f"name:{name}/error:{e}")
            try_num_get_user += 1
            continue
        else:
            exc_type = json_data.get("exc_type")
            if exc_type == "NoFreeAccounts":
                try_num_get_user += 1
                logger.warning(f"json_data:{json_data} retry-{try_num_get_user}/{max_try_num_get_user}")
                continue

            if exc_type == "InstagramServerError":
                try_num_get_user += 1
                logger.warning(f"json_data:{json_data} retry-{try_num_get_user}/{max_try_num_get_user}")
                continue

            if exc_type == "HashtagNotFound":
                logger.warning(f"존재하지 않는 hashtag")
                raise HashtagNotFound

            if json_data.get("data") is None:
                logger.error(f"name:{name}/{json_data}")
                try_num_get_user += 1
                continue
            ###response type check(Hashtag Validation)
            # else:
            #     try:
            #         Hashtag(**json_data)
            #     except Exception as e:
            #         logger.warning(f"json_data:{json_data}/{e} retry-{try_num_get_user}/{max_try_num_get_user}")
            #         try_num_get_user += 1
            #         continue
            return json_data


def send_message(account_info, user_info_list):
    max_retry_num=1
    retry_num = 0
    while True:
        if retry_num>=max_retry_num:
            return 400
        access_key = "nTYC9RbjpV8axJ3I9OnKI9Z4QVu7hzrE"
        headers = {"x-access-key": access_key}
        sessionid = account_info.get('graph_session')
        username = account_info.get('username')
        password = account_info.get('password')

        text = get_dm_source.get_source_message(filename="rounded.txt")
        userid_list = list(map(lambda x: x["userid"], user_info_list))
        data = {"sessionid": sessionid, "user_ids": userid_list, "text": f"{text}"}
        url = "https://api.lamadava.com/s1/direct/send"
        response = requests.post(url=url, data=data, headers=headers)

        if "challenge_required" in response.text:
            return 400
        if "Bad gateway" in response.text:
            return 400

        if "item_ack" in response.text:
            retry_num+=1
            logger.error(f"item_ack, retry:{retry_num}")
            continue

        time.sleep(10)
        logger.info(f"username:{username} /password:{password}/ sessionid:{sessionid} -> user_info:{user_info_list} /response:{response.text}")
        return 200


if __name__ == "__main__":
    s = get_user_profile_by_id_gpi(userid=25010806859)
    print(s)