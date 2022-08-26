import json
import requests
import time
from db import m_instagram
import logging

FORMAT = '%(module)s.%(funcName)s - %(message)s - %(levelname)s - %(asctime)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)
if logger.hasHandlers():
    # Logger is already configured, remove all handlers
    logger.handlers = []
logger.setLevel(logging.INFO)

db_conn = m_instagram.InstaDB().conn
INSTA_ACCOUNT_OBJ = m_instagram.InstaAccount(channel_name="instagram")
INSTA_ACCOUNT_OBJ.client_name = "admin_test"

def select_user(username, max_messages_per_day):
    account_setting_info = INSTA_ACCOUNT_OBJ.select_cookie_user_v2(username=username, max_messages_per_day= max_messages_per_day)
    return account_setting_info
#
def login_by_session(session_id):
    access_key = "nTYC9RbjpV8axJ3I9OnKI9Z4QVu7hzrE"
    headers = {"x-access-key": access_key}
    data = {"sessionid": session_id}
    url = "https://api.lamadava.com/s1/auth/login/by/sessionid"
    response = requests.post(url=url, data=data, headers=headers)
    data = json.loads(response.text)
    if type(data) is not str:
        print(data)
        raise AssertionError
    return response

def login(username,password):
    access_key = "nTYC9RbjpV8axJ3I9OnKI9Z4QVu7hzrE"
    headers = {"x-access-key": access_key}
    data = {"username": username, "password": password}
    url = "https://api.lamadava.com/s1/auth/login"
    response = requests.post(url=url, data=data, headers=headers)
    try:
        data = json.loads(response.text)
    except Exception as e:
        print(response.text)
        print(e)
    if type(data) is not str:
        print(data)
        raise AssertionError

    return data

def send_messages(session_id, user_ids):
    access_key = "nTYC9RbjpV8axJ3I9OnKI9Z4QVu7hzrE"
    headers = {"x-access-key": access_key}
    user_ids = list(map(lambda x: str(x), user_ids))
    user_ids = list(set(user_ids))
    print(f"user_ids : {len(user_ids)}")

    for idx, user_id in enumerate(user_ids):
        data = {"sessionid": session_id, "user_ids": [user_id], "text": f"{user_id}", }
        url = "https://api.lamadava.com/s1/direct/send"
        response = requests.post(url=url, data=data, headers=headers)
        print(idx, user_id, response.text)
        time.sleep(10)

def send_message(session_id, user_id):
    access_key = "nTYC9RbjpV8axJ3I9OnKI9Z4QVu7hzrE"
    headers = {"x-access-key": access_key}

    data = {"sessionid": session_id, "user_ids": [user_id], "text": f"{user_id}", }
    url = "https://api.lamadava.com/s1/direct/send"
    response = requests.post(url=url, data=data, headers=headers)
    print(user_id, response.text)
    time.sleep(10)

if __name__ == "__main__":
    session_id = login(username="iamjaimalikwww", password="cycwaxoi")
    # response = login_by_session("54643180776%3AjN9IuooPqRIGwA%3A16%3AAYfmOkeGnahb0uK9PViSOMf5_DTQcGcgSSWYx3CBIA")

    print(f"session_id:{session_id}")
    user_ids = [442290251, 12075911217, 25599905242, 49930227127, 49521183089, 38040276513, 1752720494, 6714060677, 49980172969, 45775449669, 1497651682, 6832024205, 38036602236, 50264745697, 1611780761, 15484575678, 3249983713, 8516740831, 397697410, 4921558923, 4013456408, 865385963, 21516442198, 50710930325, 3978534507, 2091802707, 1984899752, 9907347284, 47453074864, 3672569607, 1451852148, 44284326279, 37545831509, 2553964416, 745345129, 1435763085, 1331615215, 610138614, 1414369041, 1797549711, 1784865684, 678487220, 2087720468, 50481887559, 1598763299, 5803412950, 8037881155, 2293506548, 2288154544, 8132648038, 5878988711, 5861583524, 49291485504, 48007207452, 1750327189, 1061157663, 8762278947, 38971805458, 48252257533, 47686543734, 47961564442, 3280368310, 9266437790, 1407108861, 1471708519, 5638649494, 49240296273, 8405995706, 49993514538, 7798292140, 1747226569, 1962412674, 1473411699, 1531166403, 43104944638, 523128829, 5892498759, 4280658031, 32228590706, 14938519143, 1835808750, 3179339028, 10269942228, 2853171869, 2231259614, 44307585623, 7504139456, 50656391870, 50502486878, 50520594285, 8445251142, 40830966479, 50351073860, 2205488955, 50049744401, 3062605871, 4080779245, 47604066279, 8626014237, 782714]
    for idx, user_id in enumerate(user_ids):
        send_message(session_id=session_id, user_id=user_id)

    # "54972950573%3AHz4UiDsvtNXifR%3A26%3AAYci83thKFN8r29UL_htrCtVptbIffa-IIqrtObExw"
    # send_message(session_id)
