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
        self.redirect = False
        FORMAT = '%(module)s.%(funcName)s - %(message)s - %(levelname)s - %(asctime)s'
        logging.basicConfig(format=FORMAT)
        logger = logging.getLogger(__name__)
        if logger.hasHandlers():
            # Logger is already configured, remove all handlers
            logger.handlers = []
        logger.setLevel(logging.DEBUG)
        self.logger = logger
    @staticmethod
    def driver_setting(user_proxy=True):
        driver = get_chromedriver(use_proxy=user_proxy)
        # saves the login & pass into accounts.txt file.
        return driver

    def instagram_selenium_login(self,driver, username, password):
        engine_selenium_login.loading_page(self)
        engine_selenium_login.input_login_info(self)
        engine_selenium_login.click_login_button(self)
        engine_selenium_login.check_login_success(self)
        engine_selenium_login.check_login_success_robot(self)

    def request_login(self,driver, username,password, proxy):
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
        driver = get_chromedriver(use_proxy=True)
        login_account_info_list = botAccount_setting_db.read_account_info_from_db()
        for idx, login_account_info in enumerate(login_account_info_list):
            try:
                username = login_account_info["username"]
                password = login_account_info["password"]
                self.logger.debug(f"{idx}/{username}/{password} 로그인 시도")

                selenium_login_response = self.instagram_selenium_login(driver, username, password)
                if not selenium_login_response:
                    botAccount_setting_db.update_account_unavailable(username=username)
                    self.logger.debug(f"{username}/{password} update unavailable... we start next iteration")
                    continue

                if selenium_login_response:
                    request_login_response = self.request_login(driver, username,password, proxy)
                    self.logger.info(f"request_login_response:{request_login_response}")
            except Exception as e:
                self.logger.error(f"exception : {e}")
