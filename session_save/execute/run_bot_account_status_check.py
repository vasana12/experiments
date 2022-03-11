from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger
import logging
import time
from datetime import datetime
from session_save.setting.get_residential_driver import get_chromedriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from db import m_instagram
from session_save.setting import config
from session_save.setting.botAccount_setting_db import read_challenge_required_account_info_from_db

insta_db = m_instagram.InstaDB(db_name="account")
account_collection = insta_db.account_collection

FORMAT = '%(module)s.%(funcName)s - %(message)s - %(levelname)s - %(asctime)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)
if logger.hasHandlers():
    # Logger is already configured, remove all handlers
    logger.handlers = []
logger.setLevel(logging.DEBUG)

JIN_INSTAGRAM = m_instagram.InstaDB(db_name="instagram_analysis").db
JIN_ACCOUNT = JIN_INSTAGRAM["account"]

SERVICE_INSTAGRAM = m_instagram.InstaDB(db_name="service_instagram").db
INSTA_ACCOUNT_OBJ = m_instagram.InstaAccount(channel_name="instagram").db
ACCOUNT_COLLECTION = INSTA_ACCOUNT_OBJ['account']
BAND_ACCOUNT, HASHTAG_AND_USER, PROJECT_COLLECTION, ITEM_HASHTAG_COLLECTION, ITEM_USER_COLLECTION, ITEM_LOCATION_COLLECTION, INFO_COLLECTION, TASK_COLLECTION, POST_COLLECTION, SEARCH_COLLECTION = \
    SERVICE_INSTAGRAM["account_instagram"], SERVICE_INSTAGRAM["hashtag_and_user"], SERVICE_INSTAGRAM["project"], SERVICE_INSTAGRAM["hashtag"], \
    SERVICE_INSTAGRAM["user"], SERVICE_INSTAGRAM["location"], SERVICE_INSTAGRAM["info"], SERVICE_INSTAGRAM["task"], \
    SERVICE_INSTAGRAM["post"], SERVICE_INSTAGRAM["search"]

def main(username, password):
    def driver_setting(user_proxy=True):
        driver = get_chromedriver(use_proxy=True)
        #saves the login & pass into accounts.txt file.
        return driver

    def check_hacking(driver):
        try:
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable(
                (By.XPATH, "//*[@id='react-root']/section/main/div[2]/div/div/div[2]/div[5]/button")))
        except Exception as e:
            logger.debug(f"error_message: no element //*[@id='react-root']/section/main/div[2]/div/div/div[2]/div[5]/button")
            return False
        else:
            driver.find_element(By.XPATH,
                                "//*[@id='react-root']/section/main/div[2]/div/div/div[2]/div[5]/button").click()
            return True

    def check_ssfErrorAlert(driver):
        "//*[@id='slfErrorAlert']"
        try:
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, "//*[@id='slfErrorAlert']")))
        except Exception as e:
            logger.debug(f"not ssfErrorAlert")
            return False
        else:
            logger.debug(f"ssfErrorAlert")
            return True

    def check_cache_modal(driver):
        try:
            WebDriverWait(driver, 10).until(EC.presence_of_element_located(
                (By.XPATH, "//button[@class='aOOlW   HoLwm '] | /html/body/div[4]/div/div/div/div[3]/button[2]")))
        except Exception as e:
            logger.debug(f"button[@class='aOOlW   HoLwm '] cache modal not exist:{e}")
            return False
        else:
            WebDriverWait(driver, 10).until(EC.presence_of_element_located(
                (By.XPATH,
                 "//button[@class='aOOlW   HoLwm '] | /html/body/div[4]/div/div/div/div[3]/button[2]"))).cilck()
            return True

    def check_login_success(driver):
        try:
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH,
                                                                                 "//button[@class='sqdOP  L3NKy   y3zKF     '] | //*[@id='react-root']/section/main/div/div/div/section/div/button")))
        except Exception as e:
            logger.debug(f"sqdOP  L3NKy   y3zKF     error_message: no button //button[@class='sqdOP  L3NKy   y3zKF     '] | //*[@id='react-root']/section/main/div/div/div/section/div/button")
            return False
        else:
            csrftoken_info = driver.get_cookie("csrftoken")
            if csrftoken_info:
                logger.info("selenium login process success, we send selenium session info to request ")
                return True
            else:
                logger.info("selenium login process failed")
                return False

    def change_password(driver):
        # old_password
        try:
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable(
                (By.XPATH, "//input[@name='old_password']")))
        except Exception as e:
            logger.debug(f"error_message: no element //input[@name='old_password']")
        else:
            driver.find_element(By.XPATH, "//input[@name='old_password']").send_keys(password)

        logger.debug(f"chage_password {password} to {config.NEW_PASSWORD}")
        # new_password
        try:
            WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//input[@name='new_password1']")))
        except Exception as e:
            logger.debug(f"error_message: no element  //input[@name='new_password1']")
        else:
            driver.find_element(By.XPATH, "//input[@name='new_password1']").send_keys(config.NEW_PASSWORD)

        # check new_password
        try:
            WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//input[@name='new_password2']")))
        except Exception as e:
            logger.debug(f"error_message: no element //input[@name='new_password2']")
        else:
            driver.find_element(By.XPATH, "//input[@name='new_password2']").send_keys(config.NEW_PASSWORD)

        # click change_password_button
        try:
            WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//*[@id='react-root']/section/main/div[2]/div/div/div[2]/form/div[4]/button")))
        except Exception as e:
            logger.debug(f"error_message:{e}")
        else:
            driver.implicitly_wait(10)
            driver.find_element(By.XPATH, "//*[@id='react-root']/section/main/div[2]/div/div/div[2]/form/div[4]/button").click()
            ACCOUNT_COLLECTION.update_one(filter=
                                                                {
                                                                    "username":username
                                                                },
                                                            update=
                                                                {
                                                                    "$set":
                                                                        {
                                                                            "password":config.NEW_PASSWORD,
                                                                            "status":"available",
                                                                            "last_login": datetime.now()
                                                                        },
                                                                    }
                                                                )
    driver = driver_setting()
    # try:
    #### 1.1 인스타그램 로그인 페이지로 이동하기
    driver.get("https://www.instagram.com")
    ####로딩할 때까지 기다려준다 (10초 지나면 에러처리)
    driver.implicitly_wait(10)

    try:
       WebDriverWait(driver, 20).until(EC.visibility_of_all_elements_located((By.XPATH, "//*[@id='loginForm']/div/div[1]/div/label/input")))
    except Exception as e:
        logger.debug(f"error_message:{e}")
        time.sleep(3)
        WebDriverWait(driver, 20).until(EC.visibility_of_all_elements_located((By.XPATH, "//*[@id='loginForm']/div/div[1]/div/label/input")))
        raise Exception
    input_login = driver.find_element(By.XPATH,"//*[@id='loginForm']/div/div[1]/div/label/input")
    input_password = driver.find_element(By.XPATH,"//*[@id='loginForm']/div/div[2]/div/label/input")
    input_login.send_keys(username)
    input_password.send_keys(password)

    try:
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//*[@id='loginForm']/div/div[3]/button")))
    except Exception as e:
        logger.debug(f"error_message: no element //*[@id='loginForm']/div/div[3]/button")
    else:
        driver.find_element(By.XPATH, "//*[@id='loginForm']/div/div[3]/button").click()

    login_status = check_login_success(driver)
    if not login_status:
        if check_hacking(driver):
            logger.info("check_hacking... change_password")
            change_password(driver)
            return
        else:
            ACCOUNT_COLLECTION.update_one(filter=
            {
                "username": username
            },
                update=
                {
                    "$set":
                        {
                            "password": config.NEW_PASSWORD,
                            "status": "unavailable",
                            "last_login": datetime.now()
                        },
                }
            )
    else:
        ACCOUNT_COLLECTION.update_one(filter=
        {
            "username": username
        },
            update=
            {
                "$set":
                    {
                        "password": config.NEW_PASSWORD,
                        "status": "available",
                        "last_login": datetime.now()
                    },
            }
        )

    driver.close()
def run_macro():
    login_account_info_list = read_challenge_required_account_info_from_db()
    for idx, login_account_info in enumerate(login_account_info_list):
        login_retry = 0
        username = login_account_info["username"]
        password = login_account_info["password"]
        logger.info(f"{idx}/{username}/{password} 로그인 시도")
        try:
            main(username, password)
        except Exception as e:
            continue

if __name__ == "__main__":
    scheduler = BlockingScheduler()
    scheduler.add_job(run_macro, IntervalTrigger(seconds=3), max_instances=1)
    logging.getLogger('apscheduler.scheduler').setLevel(logging.CRITICAL+10)
    scheduler.start()