import uuid
from datetime import datetime
import requests
from setting.get_residential_driver import get_chromedriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
import time
from db import m_instagram
import logging
from setting.botAccount_setting_read import read_account_info_from_db, read_account_setting_info_from_db
from setting import config
import json
import requests.utils

insta_db = m_instagram.InstaDB(db_name="account")
account_collection = insta_db.account_collection

logger = logging.getLogger(__name__)

# 로그의 출력 기준 설정
logger.setLevel(logging.DEBUG)

# log 출력 형식
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s %(funcName)s - %(message)s')

# log 출력
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

JIN_INSTAGRAM = m_instagram.InstaDB(db_name="instagram_analysis").db
JIN_ACCOUNT = JIN_INSTAGRAM["account"]

SERVICE_INSTAGRAM = m_instagram.InstaDB(db_name="service_instagram").db
INSTA_ACCOUNT_OBJ = m_instagram.InstaAccount(channel_name="instagram").db
BAND_ACCOUNT, HASHTAG_AND_USER, PROJECT_COLLECTION, ITEM_HASHTAG_COLLECTION, ITEM_USER_COLLECTION, ITEM_LOCATION_COLLECTION, INFO_COLLECTION, TASK_COLLECTION, POST_COLLECTION, SEARCH_COLLECTION = \
    SERVICE_INSTAGRAM["account_instagram"], SERVICE_INSTAGRAM["hashtag_and_user"], SERVICE_INSTAGRAM["project"], SERVICE_INSTAGRAM["hashtag"], \
    SERVICE_INSTAGRAM["user"], SERVICE_INSTAGRAM["location"], SERVICE_INSTAGRAM["info"], SERVICE_INSTAGRAM["task"], \
    SERVICE_INSTAGRAM["post"], SERVICE_INSTAGRAM["search"]





def main(username, password):
    def success(username, password, cookie, expiry):
        setting_info = read_account_setting_info_from_db(username,password)
        logger.info(f"{username}/{password} success - > account collection")
        filter = {"username": username}
        account_info = account_collection.find_one(filter=filter)

        ## when account_already exist
        if account_info:
            _id = account_info["_id"]
            account_collection.update_one(
                filter ={
                    "_id": _id
                },
                update ={
                    "$set": {
                        "usage.hashtag": 0,
                        "usage.dm": 0,
                        "last_login": datetime.now(),
                        "status": "available",
                        "uuids": setting_info["uuids"],
                        "timing_value.last_login":time.time(),
                        "timing_value.last_experiments": time.time(),
                        "device_settings": setting_info["device_settings"],
                        "user_agent": setting_info["user_agent"],
                        "cookie": cookie,
                        "session_expire": expiry
                    }
                }
            )
            logger.info(f"{username}/{password} update finish")
            return

        ### new account setting info insert
        insert_info = {
                    "username": username,
                    "password": password,
                    "client_name": setting_info["client_name"],
                    "channel": "instagram",
                    "limit": {
                        "dm": setting_info["limit"]["dm"],
                        "hashtag": setting_info["limit"]["hashtag"]
                    },
                    "usage": {
                        "dm": 0,
                        "hashtag": 0
                    },
                    "uuids":
                        {
                            setting_info["uuids"]
                        },
                    "timing_value":
                        {
                            "last_login": time.time(),
                            "last_experiments": time.time()
                        },
                    "device_settings":setting_info["device_settings"],
                    "user_agent": setting_info["user_agent"],
                    "last_login": datetime.now(),
                    "cookie":cookie,
                    "session_expire": expiry
                    }
        account_collection.insert_one(insert_info)
        logger.info(f"{username}/{password} insert finish")

    def driver_setting(user_proxy=True):
        driver = get_chromedriver(use_proxy=user_proxy)
        #saves the login & pass into accounts.txt file.
        return driver


    driver = driver_setting()
    # try:
    #### 1.1 인스타그램 로그인 페이지로 이동하기
    driver.get("https://www.instagram.com")
    ####로딩할 때까지 기다려준다 (10초 지나면 에러처리)
    driver.implicitly_wait(10)
    try:
       WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//*[@id='react-root']/section/main/article/div/div/div/div[3]/button[1]")))
    except Exception as e:
        logger.debug(f"error_message:{e}")
        time.sleep(3)
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//*[@id='react-root']/section/main/article/div/div/div/div[3]/button[1]")))
        raise Exception
    else:
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//*[@id='react-root']/section/main/article/div/div/div/div[3]/button[1]"))).click()

    input_login = driver.find_element(By.XPATH,"//input[@name='username']")
    input_password = driver.find_element(By.XPATH,"//input[@name='password']")
    input_login.send_keys(username)
    input_password.send_keys(password)

    try:
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//*[@id='loginForm']/div[1]/div[6]/button")))
    except Exception as e:
        logger.debug(f"error_message:{e}")
    else:
        driver.find_element(By.XPATH, "//*[@id='loginForm']/div[1]/div[6]/button").click()

    time.sleep(5)
    csrftoken_info = driver.get_cookie("csrftoken")
    mid_info = driver.get_cookie("mid")
    session_id_info = driver.get_cookie("sessionid")
    ds_user_id_info = driver.get_cookie("ds_user_id")
    rur_info = driver.get_cookie("rur")

    logger.info(f"{csrftoken_info}")

    setting_info = read_account_setting_info_from_db(username, password)
    logger.info(f'csrftoken_info["value"]:{csrftoken_info["value"]}')
    data = json.dumps(
        {
            "jazoest": "22264",
            "country_codes": '[{"country_code":"1","source":["default"]}]',
            "phone_id": setting_info["uuids"]["phone_id"],
            "_csrftoken": csrftoken_info["value"],
            "username": username,
            "adid": "",
            "guid": setting_info["uuids"]["uuid"],
            "device_id": setting_info["uuids"]["device_id"],
            "google_tokens": "[]",
            "password": password,
            # "enc_password:" "#PWD_INSTAGRAM:4:TIME:ENCRYPTED_PASSWORD"
            "login_attempt_count": "0",
        }
    )

    s = requests.Session()
    s.headers.update(config.REQUEST_HEADERS)
    s.headers.update({"User-Agent":setting_info["user_agent"]})
    for cookie in driver.get_cookies():
        c = {cookie["name"]: cookie["value"]}
        s.cookies.update(c)

    response = s.post(f"{config.API_URL}accounts/login/", data=data)
    logger.info(f"response.text:{response.text}")
    logger.info(f"request_info:{requests.utils.dict_from_cookiejar(s.cookies)}")

    # if csrftoken_info and mid_info and session_id_info:
    #     cookie = {
    #         "csrftoken": csrftoken_info["value"],
    #         "ds_user_id": ds_user_id_info["value"],
    #         "mid": mid_info["value"],
    #         "rur": rur_info["value"],
    #         "sessionid": session_id_info["value"]
    #     }
    #     expiry = session_id_info["expiry"]
    #     success(username,password, cookie= cookie, expiry=expiry)
    # driver.close()
if __name__ == "__main__":
    login_account_info_list = read_account_info_from_db()
    for idx, login_account_info in enumerate(login_account_info_list[0:1]):
        login_retry = 0
        # username = login_account_info["username"]
        # password = login_account_info["password"]
        username = "distfomittspit19801979"
        password = "0ATG8pvFqr"
        logger.debug(f"{idx}/{username}/{password} 로그인 시도")
        main(username, password)
        # try:
        #
        #     main(username, password)
        # except Exception as e:
        #     try:
        #         print(f"error : {e}")
        #         main(username, password)
        #     except Exception as e:
        #         print(f"error : {e}")
        #         logger.error(f"{idx}/{username}/{password} 로그인 실패")
        #         continue
        # else:
        #     logger.error(f"{idx}/{username}/{password} 로그인 성공")
