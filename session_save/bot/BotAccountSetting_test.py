import requests
import requests.utils
from session_save.setting.get_residential_driver import get_chromedriver
import logging
from session_save.setting import config
from session_save.setting import botAccount_setting_db
from session_save.engine import engine_login
from session_save.engine import engine_selenium_login


class botAccountSetting():
    def __init__(self):
        self.login_page_redirect = False
        # FORMAT = 'INSTAGRAM_TARGETING_BOTs %(asctime)s - %(levelname)s - %(name)s - %(module)s.%(funcName)s - %(message)s'
        FORMAT = '%(module)s.%(funcName)s - %(message)s - %(levelname)s - %(asctime)s'
        logging.basicConfig(format=FORMAT)
        logger = logging.getLogger(__name__)
        if logger.hasHandlers():
            # Logger is already configured, remove all handlers
            logger.handlers = []
        logger.setLevel(logging.DEBUG)
        self.logger = logger
        self.proxy = f"http://{config.PROXY_USER}:{config.PROXY_PASS}@{config.PROXY_HOST}:{config.PROXY_PORT}"
        self.is_ssfErrorAlert = False

    @staticmethod
    def driver_setting(user_proxy=True):
        driver = get_chromedriver(use_proxy=user_proxy)
        # saves the login & pass into accounts.txt file.
        return driver

    def send_driver_cookie(self):
        s = requests.Session()
        for cookie in self.driver.get_cookies():
            c = {cookie["name"]: cookie["value"]}
            s.cookies.update(c)
        self.logger.info(f"selenium-cookie-info:{s.cookies.get_dict()}")
        self.session = s
        return True

    def request_login(self):
        login_session = engine_login.loginSession(username=self.username, password=self.password, proxy=self.proxy,
                                                  session=self.session)
        request_login_response = login_session.login()
        return request_login_response

    def instagram_selenium_loading(self):
        ###0. 로그인 페이지로 이동하기
        self.first_page_iterate_count = 0
        while True:
            self.logger.debug(f"first_page_iterate_count:{self.first_page_iterate_count}")
            if self.first_page_iterate_count >= 5:
                self.driver.close()
                self.driver = self.driver_setting()
                self.login_page_redirect = False
                engine_selenium_login.loading_page(self)
                return False

            if engine_selenium_login.loading_page(self):
                break
            else:
                self.first_page_iterate_count += 1


            # self.logger.info(f"check selenium login status")
            # self.login_page_redirect = False
            # return self.send_driver_cookie()

    def iterate_login(self):

        login_account_info_list = botAccount_setting_db.read_account_info_from_db()

        for idx, login_account_info in enumerate(login_account_info_list):
            if idx%10 == 0:
                try:
                    self.driver.close()
                except:
                    pass
                self.driver = get_chromedriver(use_proxy=True)
                self.instagram_selenium_loading()
            try:
                self.username = login_account_info["username"]
                self.password = login_account_info["password"]
                self.logger.info(f"{idx}/{self.username}/{self.password} 로그인 시도")

                selenium_login_response = self.send_driver_cookie()

                if not selenium_login_response:
                    botAccount_setting_db.update_account_unavailable(username=self.username)
                    self.logger.info(f"{self.username}/{self.password} update unavailable... we start next iteration")
                    continue

                if selenium_login_response:
                    request_login_response = self.request_login()
                    self.logger.info(f"request_login_response:{request_login_response}")
                    if request_login_response:
                        continue
                    else:
                        self.logger.info(f"+1 request_login_response:{request_login_response}")
                        self.request_login()

                    # else:
                    #     self.driver.close()
                    #     self.drvier = self.driver_setting()
                    #     self.login_page_redirect = False

            except Exception as e:
                self.logger.error(f"exception : {e}")
