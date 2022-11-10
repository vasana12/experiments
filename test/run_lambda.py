import os
import json
from datetime import datetime, timedelta, timezone
import boto3
from db import m_instagram
from collections import Counter
import pymongo
import re
import requests
import unicodedata
import requests
from urllib.parse import quote
import logging
import copy

datetime_utc = datetime.utcnow()
timezone_kst = timezone(timedelta(hours=9))

FORMAT = '%(module)s.%(funcName)s - %(message)s - %(levelname)s - %(asctime)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)
if logger.hasHandlers():
    # Logger is already configured, remove all handlers
    logger.handlers = []
logger.setLevel(logging.DEBUG)

# IMAGE_BASE_URL = "https://supertag-instagram.s3.ap-northeast-2.amazonaws.com/"
# bucket_name = "supertag-instagram"
# s3_resource = boto3.resource('s3',
#                              aws_access_key_id='AKIAVBUSUE2XLDYGOL56',
#                              aws_secret_access_key='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',
#                              region_name='ap-northeast-2')

SERVICE_INSTAGRAM = m_instagram.InstaDB(db_name="service_instagram").db
INSTA_ACCOUNT_OBJ = m_instagram.InstaAccount(client_name="admin", channel_name="instagram").db
ACCOUNT_COLLECTION = INSTA_ACCOUNT_OBJ['account']
USER_CHECKPOINT, HASHTAG_AND_USER_SEARCH, HASHTAG_AND_USER, PROJECT_COLLECTION, ITEM_HASHTAG_COLLECTION, ITEM_USER_COLLECTION, ITEM_LOCATION_COLLECTION, INFO_COLLECTION, TASK_COLLECTION, POST_COLLECTION, SEARCH_COLLECTION = \
    SERVICE_INSTAGRAM["user_checkpoint"], SERVICE_INSTAGRAM["hashtag_and_user_search"], SERVICE_INSTAGRAM[
        "hashtag_and_user"], SERVICE_INSTAGRAM["project"], \
    SERVICE_INSTAGRAM["hashtag"], \
    SERVICE_INSTAGRAM[
        "user"], SERVICE_INSTAGRAM["location"], SERVICE_INSTAGRAM["info"], SERVICE_INSTAGRAM["task"], SERVICE_INSTAGRAM[
        "post"], SERVICE_INSTAGRAM["search"]

dicdir = os.path.join("/opt/python", 'local', 'lib', 'mecab', 'dic', 'mecab-ko-dic')
rcfile = os.path.join("/opt/python", 'local', 'etc', 'mecabrc')

stopKeywordList = ['likeforlikes', 'insta', '데일리룩', '셀스타그램', 'sale', '오오티디', 'ootdfashion', 'daily', 'instadaily',
                   'instagood', 'secla', '오피',
                   'ootd', 'dailylook', "셀스타그램", "selfie", "맞팔", "팔로우", "좋아요",
                   "일상", "행복", "f4f", "그램", "구매", "문의", "주세요", "ㅎㅎ다", "ㅎㅎㅎ다", "ㅋㅋㅋ다", "ㅋㅋ다", "인스"]


def count(sentence_list):
    counter = Counter(sentence_list)
    most_common = counter.most_common()
    most_common = list(filter(lambda c: len(c[0]) >= 2, most_common))
    most_common = list(filter(lambda c: c[0] not in stopKeywordList, most_common))
    most_common = list(map(lambda c: c[0], most_common))
    most_common = most_common[0:10]
    most_common = list(map(lambda hashtag: "#" + hashtag, most_common))
    most_common = ", ".join(most_common)
    return most_common


def insert_db(response_data):
    nouns_hashtag = f"{response_data.get('caption_hashtag')},{response_data.get('nouns')}, #{response_data.get('hashtag')},#{response_data.get('username')}"
    nouns_hashtag = nouns_hashtag.replace(" ", "")
    nouns_hashtag = nouns_hashtag.split(",")
    nouns_hashtag = set(nouns_hashtag)
    nouns_hashtag = ", ".join(nouns_hashtag)
    search_content = f"{nouns_hashtag}, {response_data.get('adjectives')}"
    search_content = search_content.replace(",", "")
    datetime_now = datetime.now() + timedelta(hours=9)
    response_data.update(search_content=search_content)
    response_data.update(status="analyzed_done")
    response_data.update(analyzed_date_time=datetime_now)
    USER_CHECKPOINT.insert_one(response_data)


def update_db(response_data):
    nouns_hashtag = f"{response_data.get('caption_hashtag')},{response_data.get('nouns')}, #{response_data.get('hashtag')},#{response_data.get('username')}"
    nouns_hashtag = nouns_hashtag.replace(" ", "")
    nouns_hashtag = nouns_hashtag.split(",")
    nouns_hashtag = set(nouns_hashtag)
    nouns_hashtag = ", ".join(nouns_hashtag)
    search_content = f"{nouns_hashtag}, {response_data.get('adjectives')}"
    search_content = search_content.replace(",", "")

    datetime_now = datetime.now() + timedelta(hours=9)
    response_data.update(search_content=search_content)
    response_data.update(status="analyzed_done")
    response_data.update(analyzed_date_time=datetime_now)

    update_filter = {"username": response_data.get("username")}
    update = {"$set": response_data}
    USER_CHECKPOINT.update_one(filter=update_filter, update=update)


def lambda_handler(event, context):
    def get_user_biograhpy(json_data):
        try:
            return json_data["biography"]
        except:
            return None

    def get_user_external_url(json_data):
        try:
            return json_data["external_url"]
        except:
            return None

    def get_user_followed_by(json_data):
        try:
            return json_data["edge_followed_by"]["count"]
        except:
            return None

    def get_user_follow(json_data):
        try:
            return json_data["edge_follow"]["count"]
        except:
            return None

    def get_user_mediacount(json_data):
        try:
            return json_data["edge_owner_to_timeline_media"]["count"]
        except:
            return None

    def get_caption_hashtag(json_data):
        hashtag_list = []
        for idx, node in enumerate(json_data["edge_owner_to_timeline_media"]["edges"]):
            node = node["node"]
            caption = node["edge_media_to_caption"]["edges"]
            if len(caption) == 0:
                continue
            caption = caption[0]["node"]["text"]
            caption = caption.replace("\n", "")
            caption = unicodedata.normalize('NFC', caption)
            hashtag_regex = re.compile(r"(?:#)(\w(?:(?:\w|(?:\.(?!\.))){0,28}(?:\w))?)")
            hashtags = re.findall(hashtag_regex, caption.lower())
            hashtag_list.extend(hashtags)
        return count(hashtag_list)

    def get_avg(json_data):
        try:
            total_likes = 0
            total_comments = 0
            for idx, node in enumerate(json_data["edge_owner_to_timeline_media"]["edges"]):
                node = node["node"]
                comments = int(node["edge_media_to_comment"]["count"])
                likes = int(node["edge_liked_by"]["count"])
                total_likes += likes
                total_comments += comments
            contents_num = len(json_data["edge_owner_to_timeline_media"]["edges"])
            avg_likes = round(total_likes / contents_num)
            avg_comments = round(total_comments / contents_num)
        except Exception:
            return None, None
        return avg_likes, avg_comments

    def get_text(json_data):
        noun_list = []
        adjective_list = []
        for idx, node in enumerate(json_data["edge_owner_to_timeline_media"]["edges"]):
            node = node["node"]
            caption = node["edge_media_to_caption"]["edges"]
            if len(caption) == 0:
                continue
            caption = caption[0]["node"]["text"]
            caption = caption.replace("\n", "")

        adjective_list = [a + "다" for a in adjective_list]
        return count(noun_list), count(adjective_list)

    def upload_profile(profile_url):
        # profile_file_name = profile_url.split("/")[-1]
        # profile_req_for_image = requests.get(profile_url, stream=True)
        # profile_file_object_from_req = profile_req_for_image.raw
        # profile_req_data = profile_file_object_from_req.read()

        # s3_resource.Bucket(bucket_name).put_object(Key=f"profile/{profile_file_name}",
        #                                           Body=profile_req_data, ACL='public-read',
        #                                           ContentType="image/jpg")
        return profile_url

    # def get_user_raw_data(username):
    #     headers = {'x-ig-app-id': '936619743392459'}
    #     params = {'username': f'{username}'}
    #     response = requests.get('https://i.instagram.com/api/v1/users/web_profile_info/', params=params,
    #                     headers=headers)
    #     json_data = json.loads(response.text)
    #     print(json_data)
    #     data = json_data["data"]["user"]
    #     return data

    def json_value(data, *args, default=None):
        cur = data
        for a in args:
            try:
                if isinstance(a, int):
                    cur = cur[a]
                else:
                    cur = cur.get(a)
            except (IndexError, KeyError, TypeError, AttributeError):
                return default
        return cur

    def get_user_info_by_name(username):
        max_try_num_get_user = 5
        try_num_get_user = 0
        while True:
            if try_num_get_user > max_try_num_get_user:
                logger.warning(f"LamadavaServerError")
                raise ConnectionError

            try:
                access_key = "nTYC9RbjpV8axJ3I9OnKI9Z4QVu7hzrE"
                headers = {"x-access-key": access_key}
                params = {"username": username}
                response = requests.get(url="https://api.lamadava.com/a1/user", params=params, headers=headers)
                data = json.loads(response.text)
                # json_data = json_value(data, "graphql", "user")
                json_data = data
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
                    raise ConnectionError

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
        return response

    def send_request(username):
        max_try_num_get_user = 10
        try_num_get_user = 0
        while True:
            if try_num_get_user > max_try_num_get_user:
                logger.warning(f"LamadavaServerError")
                raise ConnectionError

            try:
                access_key = "nTYC9RbjpV8axJ3I9OnKI9Z4QVu7hzrE"
                headers = {"x-access-key": access_key}
                params = {"username": username}
                response = requests.get(url="https://api.lamadava.com/a1/user", params=params, headers=headers)

                data = json.loads(response.text)
                # json_data = json_value(data, "graphql", "user")
                json_data = data
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
                    raise ConnectionError

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

    def get_all_data(username):

        try:
            json_data = send_request(username=username)

            try:
                json_data = json_data["data"]["user"]
            except:
                json_data = json_data["graphql"]["user"]
        except Exception as e:
            raise e

        is_private = json_data["is_private"]
        userid = json_data["id"]
        profile_pic_url = json_data["profile_pic_url"]
        user_followed_by = get_user_followed_by(json_data)
        user_follow = get_user_follow(json_data)
        mediacount = int(get_user_mediacount(json_data))
        user_biography = get_user_biograhpy(json_data)
        user_external_url = get_user_external_url(json_data)
        avg_like, avg_comment = 'null', 'null'

        if not is_private and mediacount > 0:
            avg_like, avg_comment = get_avg(json_data)
        try:
            nouns_ranked, adjectives_ranked = get_text(json_data)
        except:
            nouns_ranked, adjectives_ranked = '', ''
        try:
            caption_hashtag = get_caption_hashtag(json_data)
        except:
            caption_hashtag = ''
        all_data = {"is_private": is_private, "profile_url": profile_pic_url, "userid": str(userid),
                    "mediacount": mediacount,
                    "caption_hashtag": caption_hashtag, "nouns": nouns_ranked, "adjectives": adjectives_ranked,
                    "avg_comment": avg_comment, "avg_like": avg_like, "user_biography": user_biography,
                    "user_external_url": user_external_url, "user_follow": user_follow,
                    "user_followed_by": user_followed_by}
        return all_data

    username = event.get("username")
    print(username)
    hashtag = event.get("hashtag")
    headers = event.get("headers")
    cookies = event.get("cookies")

    checkpoint_update_term = event.get("checkpoint_update_term")
    if checkpoint_update_term is None:
        checkpoint_update_term = 30

    response_data = {}

    logger.debug(f"response_data:{response_data}")
    try:
        item_user_doc = ITEM_USER_COLLECTION.find_one({"username": username})

        # 1 - 데이터 처리

        # 1.1 이미 유저가 존재하는 경우
        if item_user_doc:
            logger.debug("## user 가 존재한다.")
            ## user checkpoint 가 존재하는지 확인한다.
            user_checkpoint_doc = USER_CHECKPOINT.find_one({"username": username}, {"_id": 0})
            logger.debug("## user checkpoint 가 존재하는지 확인한다.")

            ## 1.1.1 user checkpoint 가 존재한다.
            if user_checkpoint_doc:
                added_hashtag = user_checkpoint_doc["hashtag"]
                logger.debug("## user checkpoint 가 존재한다.")
                ### 한달 지낫는지 체크
                logger.debug(f"## checkpoint 가 {checkpoint_update_term} 일 지낫는지 체크")
                analyzed_date_time = user_checkpoint_doc["analyzed_date_time"]

                if analyzed_date_time:
                    user_checkpoint_date = user_checkpoint_doc["analyzed_date_time"].date()
                else:
                    user_checkpoint_date = datetime.now(tz=timezone_kst).date() - timedelta(
                        days=checkpoint_update_term + 1)
                checkpoint_update_time = datetime.now(tz=timezone_kst).date() - timedelta(days=checkpoint_update_term)

                logger.debug(f"마지막 분석 시점 : {user_checkpoint_date}")
                logger.debug(f"업데이트 기준 날짜 : {checkpoint_update_time}")

                ### 1.1.1.1  checkpoint 가 텀을 지난 경우
                if user_checkpoint_date < checkpoint_update_time:
                    logger.debug(f"## checkpoint 가 {checkpoint_update_term}일 지난 경우 user_checkpoint 에서 업데이트 시켜준다.")
                    #### user_checkpoint 에서 업데이트 시켜준다.
                    response_data = get_all_data(username)
                    response_data.update(username=username, hashtag=hashtag)

                    ###added_hashtag
                    added_hashtag = user_checkpoint_doc["hashtag"]
                    response_caption_hashtag = response_data["caption_hashtag"]
                    response_data["caption_hashtag"] = f"{response_caption_hashtag}, #{added_hashtag}"
                    last_response_data = response_data.copy()
                    update_db(response_data)
                    return {'statusCode': 200, 'body': last_response_data}

                ### 1.1.1.2 텀이 안된 게시물인 경우 업데이트 하지 않는다.
                else:
                    try:
                        del user_checkpoint_doc["search_content"]
                        del user_checkpoint_doc["status"]
                        del user_checkpoint_doc["analyzed_date_time"]
                    except Exception as e:
                        pass
                    logger.debug(f"## {checkpoint_update_term}이 안된 게시물인 경우 업데이트 하지 않는다.")
                    return {'statusCode': 200, 'body': user_checkpoint_doc}

            ## 1.1.2 user checkpoint 가 존재하지 않는 경우.

            else:
                logger.debug("## user checkpoint 가 존재하지 않는 경우. insert 해준다")
                ### insert 해준다
                response_data = get_all_data(username)
                response_data.update(username=username, hashtag=hashtag)
                last_response_data = response_data.copy()

                insert_db(response_data)
                return {'statusCode': 200, 'body': last_response_data}

        # 1.2 유저가 아이템에 존재하지 않는 경우
        else:
            logger.debug("## user item 이 존재하지 않는다.")
            logger.debug("## user item 에 존재하지 않는 경우. get_all_data() 함수를 실행 해준다")
            response_data = get_all_data(username)
            response_data.update(username=username, hashtag=hashtag)
            last_response_data = response_data.copy()

            ##아이템에 데이터 삽입
            logger.debug("## user item  생성")
            ITEM_USER_COLLECTION.insert_one({"pk": str(response_data.get("userid")), "username": username})

            logger.debug("## user checkpoint  생성 해준다")
            ##체크포인트에 데이터 삽입
            insert_db(response_data)
            return {'statusCode': 200, 'body': last_response_data}

    except Exception as e:

        return {
            'statusCode': 400,
            'body': f"error:{e}"
        }

event ={
  "hashtag": "레뷰체험단",
  "username": "eunnagil",
  "checkpoint_update_term": -5
}
res = lambda_handler(event=event, context=None)
print(res)

