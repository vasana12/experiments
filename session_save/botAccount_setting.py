import requests
import requests.utils
from setting.get_residential_driver import get_chromedriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
import time
from db import m_instagram
import logging
from session_save.setting import config
from setting.botAccount_setting_db import read_account_info_from_db
from session_save.engine import engine_login

FORMAT = 'INSTAGRAM_TARGETING_BOTs %(asctime)s - %(levelname)s - %(name)s - %(module)s.%(funcName)s - %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def driver_setting(user_proxy=True):
    driver = get_chromedriver(use_proxy=user_proxy)
    # saves the login & pass into accounts.txt file.
    return driver

def instagram_selenium_login(driver, username, password):

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
        return False
    try:
        input_login = driver.find_element(By.XPATH,"//*[@id='loginForm']/div/div[1]/div/label/input")
        input_password = driver.find_element(By.XPATH,"//*[@id='loginForm']/div/div[2]/div/label/input")
        input_login.send_keys(username)
        input_password.send_keys(password)
    except Exception as e:
        logger.debug(f"error_message:{e}")
        return False

    try:
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//*[@id='loginForm']/div/div[3]/button")))
    except Exception as e:
        logger.debug(f"error_message:{e}")
        return False
    else:
        driver.find_element(By.XPATH, "//*[@id='loginForm']/div/div[3]/button").click()

    try:
        WebDriverWait(driver,10).until(EC.presence_of_element_located((By.XPATH, "//button[@class='sqdOP  L3NKy   y3zKF     '] | //*[@id='react-root']/section/main/div/div/div/section/div/button")))
    except Exception as e:
        logger.debug(f"error_message:{e}")
        return False
    else:
        csrftoken_info = driver.get_cookie("csrftoken")
        if csrftoken_info:
            logger.info("selenium login process success, we send selenium session info to request ")
            return True
        else:
            logger.info("selenium login process failed")
            return False

def request_login(driver, username,password, proxy):
    s = requests.Session()
    for cookie in driver.get_cookies():
        c = {cookie["name"]: cookie["value"]}
        s.cookies.update(c)
    logger.info(f"selenium-cookie-info:{s.cookies.get_dict()}")
    login_session = engine_login.loginSession(username=username, password=password, proxy=proxy, session=s)
    request_login_response = login_session.login()
    return request_login_response

def iterate_login():
    proxy = f"http://{config.PROXY_USER}:{config.PROXY_PASS}@{config.PROXY_HOST}:{config.PROXY_PORT}"

    login_account_info_list = read_account_info_from_db()
    for idx, login_account_info in enumerate(login_account_info_list[0:1]):
        login_retry = 0
        username = "send_direct_items"
        password = "AhfmseK2!"
        logger.debug(f"{idx}/{username}/{password} 로그인 시도")
        # try:
        driver = get_chromedriver(use_proxy=True)
        selenium_login_response = instagram_selenium_login(driver, username, password)
        if selenium_login_response:
            request_login_response = request_login(driver, username,password, proxy)
            logger.info(f"request_login_response:{request_login_response}")
iterate_login()