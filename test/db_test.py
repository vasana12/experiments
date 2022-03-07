import requests
import requests.utils
from session_save.setting.get_residential_driver import get_chromedriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
import time
from db import m_instagram
import logging
from session_save.setting import config
from session_save.setting import botAccount_setting_db
from session_save.engine import engine_login
from session_save.engine import engine_selenium_login


class botAccountSetting():
    def __init__(self):
        self.redirect = False
        FORMAT = 'INSTAGRAM_TARGETING_BOTs %(asctime)s - %(levelname)s - %(name)s - %(module)s.%(funcName)s - %(message)s'
        logging.basicConfig(format=FORMAT)
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.DEBUG)
        self.logger = logger

    @staticmethod
    def driver_setting(user_proxy=True):
        driver = get_chromedriver(use_proxy=user_proxy)
        # saves the login & pass into accounts.txt file.
        return driver

    def instagram_selenium_login(self):

        ###0. 로그인 페이지로 이동하기
        while engine_selenium_login.loading_page(self):
            return engine_selenium_login.loading_page(self)

        ###1. 로그인 정보 입력하기
        if not engine_selenium_login.input_login_info(self):
            return False

        ###2. 로그인 버튼 클릭
        if not engine_selenium_login.click_login_button(self):
            return False

        ###3. 셀레늄 로그인 성공/실패 확인
        if not engine_selenium_login.check_login_success(self):
            return False

        ###4. 계정이 봇으로 감지되었을시 로그아웃
        if not engine_selenium_login.check_login_success_robot(self):
            return False

    def request_login(self, driver, username, password, proxy):
        s = requests.Session()
        for cookie in driver.get_cookies():
            c = {cookie["name"]: cookie["value"]}
            s.cookies.update(c)
        self.logger.info(f"selenium-cookie-info:{s.cookies.get_dict()}")
        login_session = engine_login.loginSession(username=username, password=password, proxy=proxy, session=s)
        request_login_response = login_session.login()
        return request_login_response

    def iterate_login(self):
        proxy = f"http://{config.PROXY_USER}:{config.PROXY_PASS}@{config.PROXY_HOST}:{config.PROXY_PORT}"
        self.driver = get_chromedriver(use_proxy=True)
        login_account_info_list = botAccount_setting_db.read_account_info_from_db()
        for idx, login_account_info in enumerate(login_account_info_list):
            try:
                self.username = login_account_info["username"]
                self.password = login_account_info["password"]
                self.logger.debug(f"{idx}/{self.username}/{self.password} 로그인 시도")

                selenium_login_response = self.instagram_selenium_login(self.driver, self.username, self.password)
                if not selenium_login_response:
                    botAccount_setting_db.update_account_unavailable(username=self.username)
                    self.logger.debug(f"{self.username}/{self.password} update unavailable... we start next iteration")
                    continue

                if selenium_login_response:
                    request_login_response = self.request_login(self.driver, self.username, self.password, proxy)
                    self.logger.info(f"request_login_response:{request_login_response}")
            except Exception as e:
                self.logger.error(f"exception : {e}")
