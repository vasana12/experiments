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
        self.driver = get_chromedriver(use_proxy=True)
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

    def instagram_selenium_login(self):
        ###0. 로그인 페이지로 이동하기
        self.first_page_iterate_count = 0
        while True:
            self.logger.debug(f"first_page_iterate_count:{self.first_page_iterate_count}")
            if (self.is_ssfErrorAlert == True) or (self.first_page_iterate_count >=1):
                self.logger.debug(f"fself.is_ssfErrorAlert:{self.is_ssfErrorAlert}/self.first_page_iterate_count:{self.first_page_iterate_count}")
                self.driver.close()
                self.driver = self.driver_setting()
                self.login_page_redirect = False
                self.is_ssfErrorAlert = False
                if engine_selenium_login.loading_page(self):
                    break

            if engine_selenium_login.loading_page(self):
                break
            else:
                self.first_page_iterate_count += 1

        ###1. 로그인 정보 입력하기
        self.logger.info(f"input login info {self.username}/{self.password}")
        if not engine_selenium_login.input_login_info(self):

            return False

        ###2. 로그인 버튼 클릭
        self.logger.info(f"click login button")
        if not engine_selenium_login.click_login_button(self):
            return False

        ###3. 셀레늄 로그인 성공/실패 확인
        self.logger.info(f"check selenium login status")
        login_status = engine_selenium_login.check_login_success(self)

        ###로그인이 실패했을 경우
        if not login_status:
            ### check is cache modal exist
            is_cache_modal = engine_selenium_login.check_cache_modal(self)
            if is_cache_modal:
                self.logger.info(f"selenium login - success : cache modal click")
                self.login_page_redirect = False
                return self.send_driver_cookie()

            ### check is_ssfErrorAlert
            is_ssfErrorAlert = engine_selenium_login.check_ssfErrorAlert(self)
            if is_ssfErrorAlert:
                self.logger.info(f"selenium login - {login_status} : is_ssfErrorAlert, we recur instagram_selenium_login ")
                self.is_ssfErrorAlert = True
                self.instagram_selenium_login()

            ### 로봇으로 감지됐을 경우 로그아웃을 해준다.
            if engine_selenium_login.is_detected_robot(self):
                self.logger.info(f"selenium login - {login_status} : bot_detected")
                is_logout_btn = engine_selenium_login.detected_robot_logout(self)

                if is_logout_btn:
                    logout_response = engine_selenium_login.detected_robot_logout_click(self)
                    if logout_response:
                        self.login_page_redirect = True
                        return False
                    else:
                        self.login_page_redirect = False
                        return False
                else:
                    self.login_page_redirect = False
                    return False
        ###로그인이 성공했을 경우 session 정보 저장해준다.
        else:
            self.logger.info(f"check selenium login status")
            self.login_page_redirect = False
            return self.send_driver_cookie()

    def login(self):
        # self.driver = get_chromedriver(use_proxy=True)
        login_account_info = botAccount_setting_db.read_accoun_info_from_db_one()
        try:
            self.username = login_account_info["username"]
            self.password = login_account_info["password"]
            # self.username = "cendrocdanilova8dobryakova"
            # self.password = "s3BdrMcD"

            self.logger.info(f"/{self.username}/{self.password} 로그인 시도")

            selenium_login_response = self.instagram_selenium_login()

            if not selenium_login_response:
                botAccount_setting_db.update_account_unavailable(username=self.username)
                self.logger.info(f"{self.username}/{self.password} update unavailable... we start next iteration")


            if selenium_login_response:
                request_login_response = self.request_login()
                self.logger.info(f"request_login_response:{request_login_response}")
                if engine_selenium_login.success_bot_account_logout(self):
                    self.logger.debug("success_bot_account_logout - test")
                    if engine_selenium_login.success_bot_account_logout_click(self):
                        self.logger.debug("success_bot_account_logout_click - test")
                        self.login_page_redirect = True
                    else:
                        self.driver.close()
                        self.drvier = self.driver_setting()
                        self.login_page_redirect = False
        except Exception as e:
            self.logger.error(f"exception : {e}")
