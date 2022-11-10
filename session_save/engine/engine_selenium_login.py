import time

from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from session_save.bot import BotAccountSetting

def loading_page(self:BotAccountSetting):
    ### when we need to make driver go to https://www.instagram.com
    self.logger.info(f"when we need to make driver go to https://www.instagram.com - redirect {self.login_page_redirect}")
    if not self.login_page_redirect:
        try:
            self.driver.get("https://www.instagram.com")
        except Exception as e:
            self.logger.debug(f"{self.login_page_redirect}/error_message:{e}")
            self.driver.close()
            self.login_page_redirect = False
            self.driver = self.driver = self.driver_setting()
            loading_page(self)

        ####로딩할 때까지 기다려준다 (10초 지나면 에러처리)
        try:
            WebDriverWait(self.driver, 20).until(
                EC.visibility_of_all_elements_located(
                    (By.XPATH, "//*[@id='loginForm']/div/div[1]/div/label/input")))
        except Exception as e:
            self.logger.debug(f"error_message:{e}")
            self.login_page_redirect = False
            return False
        else:
            return True

    ### when we don't need to make driver go to https://www.instagram.com
    elif self.login_page_redirect:
        try:
            WebDriverWait(self.driver, 20).until(
                EC.visibility_of_all_elements_located(
                    (By.XPATH, "//*[@id='loginForm']/div/div[1]/div/label/input")))
        except Exception as e:
            self.logger.debug(f"error_message:{e}")
            self.login_page_redirect = False
            return False
        else:
            return True

def input_login_info(self:BotAccountSetting):
    # try:
    #### 1.1 인스타그램 로그인 페이지로 이동하기
    try:
        input_login = self.driver.find_element(By.XPATH,"//*[@id='loginForm']/div/div[1]/div/label/input")
        input_password = self.driver.find_element(By.XPATH,"//*[@id='loginForm']/div/div[2]/div/label/input")
        input_login.send_keys(self.username)
        input_password.send_keys(self.password)
    except Exception as e:
        self.logger.debug(f"error_message:{e}")
        return False
    else:
        return True
def click_login_button(self):
    try:
        button = WebDriverWait(self.driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//*[@id='loginForm']/div/div[3]/button")))
    except Exception as e:
        self.logger.debug(f"first method to login button find failed:{e}")
        try:
            WebDriverWait(self.driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//div[text()='로그인']")))
            self.driver.find_element(By.XPATH, "//div[text()='로그인']").click()
        except:
            self.logger.error(f"error_message click_login_button:{e}")
            return False
        else:
            return True
    else:
        try:
            self.driver.execute_script('arguments[0].click()', button)
        except Exception as e:

            return False
        return True


def check_ssfErrorAlert(self):
    "//*[@id='slfErrorAlert']"

    try:
        WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located((By.XPATH, "//*[@id='slfErrorAlert']")))
        message = self.driver.find_element(By.XPATH, "//*[@id='slfErrorAlert']").text
        self.logger.debug(f"ssfErrorAlert message:{message}")
        if "https://help.instagram.com/521372114683554" in str(message):
            self.logger.debug(f"viloation")
            return "violation"
        if "잘못된 비밀번호입니다" or "입력한 사용자 이름을 사용하는 계정을 찾을 수 없습니다." in str(message):
            self.logger.debug(f"not vaild account")
            return "invaild account"
        if "Instagram에 로그인하는 중 문제가 발생했습니다. 잠시 후 다시 시도해주세요." in str(message):
            self.logger.info(f"bad_proxy")
            return "bad_proxy"

    except Exception as e:
        self.logger.debug(f"not ssfErrorAlert")
        return False
    else:
        self.logger.debug(f"ssfErrorAlert")
        return True

def check_cache_modal(self):
    try:
        WebDriverWait(self.driver, 15).until(EC.presence_of_element_located(
            (By.XPATH, "//button[@class='aOOlW  bIiDR  ']")))
    except Exception as e:
        self.logger.debug(f"button[@class='aOOlW  bIiDR  '] cache modal not exist:{e}")
        return False
    else:
        self.driver.find_element(By.XPATH, "//button[@class='aOOlW  bIiDR  ']").click()
        return True

def check_spam_image(self):
    try:
        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, "//button[@class='sqdOP  L3NKy   y3zKF   cB_4K  ']")))
    except Exception as e:
        self.logger.debug(f"button[@class='sqdOP  L3NKy   y3zKF   cB_4K  '] check_spam_image not exist:{e}")
        return False
    else:
        self.driver.find_element(By.XPATH, "//button[@class='sqdOP  L3NKy   y3zKF   cB_4K  ']").click()
        return True

def check_login_success(self):
    try:
        # input()
        # WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, "//span[@class='coreSpriteKeyhole']")))
        '//div[@class="some-class"]/*[name()="svg"][@aria-label="Search"]'
        WebDriverWait(self.driver, 15).until(EC.presence_of_element_located((By.XPATH, "div[@class='_aa57']/*[name()='svg'][@class='_ab6-'] | //div[text()='로그인 정보를 저장하시겠어요?']")))
        # WebDriverWait(self.driver, 15).until(EC.presence_of_element_located((By.XPATH, "//div[text()='로그인 정보를 저장하시겠어요?']")))
    except Exception as e:
        self.logger.error(f"로그인 클릭 버튼 찾지 못함:{e}")
        # if check_spam_image(self):
        #     return True
        # else:
        #     return False
        return False
    else:
        csrftoken_info = self.driver.get_cookie("csrftoken")
        if csrftoken_info:
            self.logger.info("selenium login process success, we send selenium session info to request ")
            return True
        else:
            self.logger.info("selenium login process failed")
            return False

def is_detected_robot_red(self):
    try:
        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, "//button[@class='_5f5mN       jIbKX KUBKM      yZn4P   ']")))
    except Exception as e:
        self.logger.debug(f"error_message:{e}")
        return False
    else:
        return True



def is_detected_robot_red_logout_click(self):
    try:
        self.driver.find_element(By.XPATH,"//href[@class='_6vuJt']").click()
    except Exception as e:
        self.logger.debug(f"is_detected_robot_red_logout:{e}")
        return False
    else:
        return True
def is_detected_robot(self):
    try:
        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, "//button[@class='sqdOP yWX7d y3zKF '] | //*[@id='react-root']/section/main/div[1]/div/div[2]/button")))
    except Exception as e:
        self.logger.debug(f"error_message:{e}")
        return False
    else:
        return True

def detected_robot_logout(self):
    try:
        self.driver.find_element(By.XPATH,"//button[@class='sqdOP yWX7d y3zKF '] | //*[@id='react-root']/section/main/div[1]/div/div[2]/button").click()
    except Exception as e:
        self.logger.debug(f"error_message:{e}")
        return False
    else:
        return True

def detected_robot_logout_click(self):
    try:

        WebDriverWait(self.driver, 20).until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[7]/div/div/div/div[2]/button[1] | //button[@class='aOOlW  bIiDR  ']")))
    except Exception as e:
        self.logger.debug(f"error_message:{e}")
        return False
    else:
        try:
            self.driver.find_element(By.XPATH, "/html/body/div[7]/div/div/div/div[2]/button[1] | //button[@class='aOOlW  bIiDR  ']").click()
        except:
            return False
        return True

def success_bot_account_cookie_check(self):
    try:
        WebDriverWait(self.driver, 5).until(EC.element_to_be_clickable((By.XPATH, "//span[text()='모든 쿠키 허용']")))
    except Exception as e:
        self.logger.debug(f"success_bot_account_cookie_check error_message:{e}")
        pass
    else:
        self.driver.find_element(By.XPATH, "//span[text()='모든 쿠키 허용']").click()
        return True

def success_bot_account_logout(self):
    try:
        self.logger.info("로그아웃 버튼 찾기")
        WebDriverWait(self.driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//img[contains(@alt, '프로필 사진') and @class = 'xh8yej3 x11njtxf xkhd6sd x18d9i69 x4uap5 xexx8yu x1mh8g0r xat24cr x11i5rnm xdj266r xpdipgo x5yr21d xk390pu xav7gou xaqea5y x1b1mbwd x6umtig'] | //img[contains(@alt, '프로필 사진') and @class = '_aa8j'] | //div[@class='x9f619 xxk0z11 xvy4d1p x11xpdln xii2z7h x19c4wfv']/*[name()='svg'][@aria-label='설정'] | //img[@class='_6q-tv'] | //*[@id='react-root']/section/nav/div[2]/div/div/div[3]/div/div[6]/span/img | //*[@id='react-root']/div/div/section/nav/div[2]/div/div/div[3]/div/div[6]/span/img")))
    except Exception as e:
        self.logger.info(f"로그아웃 버튼 찾기 실패 error_message:{e}")
        try:
            WebDriverWait(self.driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//img[contains(@alt, '프로필 사진') and @class = 'xh8yej3 x11njtxf xkhd6sd x18d9i69 x4uap5 xexx8yu x1mh8g0r xat24cr x11i5rnm xdj266r xpdipgo x5yr21d xk390pu xav7gou xaqea5y x1b1mbwd x6umtig'] | //div[@class='x9f619 xxk0z11 xvy4d1p x11xpdln xii2z7h x19c4wfv']/*[name()='svg'][@aria-label='설정'] | //img[@class='_6q-tv'] | //*[@id='react-root']/section/nav/div[2]/div/div/div[3]/div/div[6]/span/img | //*[@id='react-root']/div/div/section/nav/div[2]/div/div/div[3]/div/div[6]/span/img")))
        except Exception as e:
            self.logger.info(f"로그아웃 버튼 찾기 실패2  error_message:{e}")
            return False
        else:
            self.logger.info(f"로그아웃 버튼 찾기 success2")
            self.driver.find_element(By.XPATH, "//img[contains(@alt, '프로필 사진') and @class = 'xh8yej3 x11njtxf xkhd6sd x18d9i69 x4uap5 xexx8yu x1mh8g0r xat24cr x11i5rnm xdj266r xpdipgo x5yr21d xk390pu xav7gou xaqea5y x1b1mbwd x6umtig'] | //div[@class='x9f619 xxk0z11 xvy4d1p x11xpdln xii2z7h x19c4wfv']/*[name()='svg'][@aria-label='설정'] | //img[@class='_6q-tv'] | //*[@id='react-root']/section/nav/div[2]/div/div/div[3]/div/div[6]/span/img | //*[@id='react-root']/div/div/section/nav/div[2]/div/div/div[3]/div/div[6]/span/img").click()
            return True
    else:
        self.logger.info(f"로그아웃 버튼 찾기 success ")
        self.driver.find_element(By.XPATH, "//img[contains(@alt, '프로필 사진') and @class = 'xh8yej3 x11njtxf xkhd6sd x18d9i69 x4uap5 xexx8yu x1mh8g0r xat24cr x11i5rnm xdj266r xpdipgo x5yr21d xk390pu xav7gou xaqea5y x1b1mbwd x6umtig'] | //img[contains(@alt, '프로필 사진') and @class = '_aa8j'] | //div[@class='x9f619 xxk0z11 xvy4d1p x11xpdln xii2z7h x19c4wfv']/*[name()='svg'][@aria-label='설정'] | //img[@class='_6q-tv'] | //*[@id='react-root']/section/nav/div[2]/div/div/div[3]/div/div[6]/span/img | //*[@id='react-root']/div/div/section/nav/div[2]/div/div/div[3]/div/div[6]/span/img").click()
        return True

def authorize_cookie(self):
    try:
        WebDriverWait(self.driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//button[@class='aOOlW  bIiDR  '] | /html/body/div[4]/div/div/button[2]")))
    except Exception as e:
        self.logger.debug(f"no authorize cookie button:{e}")
        return False
    else:
        self.driver.find_element(By.XPATH, "//button[@class='aOOlW  bIiDR  '] | /html/body/div[4]/div/div/button[2]").click()
        return True

def weird_account(self):
    try:
        WebDriverWait(self.driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//*[@id='react-root']/section/div/div/div[4]/a")))
    except Exception as e:
        self.logger.debug(f"no authorize cookie button:{e}")
        return False
    else:
        self.driver.find_element(By.XPATH, "//*[@id='react-root']/section/div/div/div[4]/a").click()
        return True

def success_bot_account_logout_click(self):

    try:
        WebDriverWait(self.driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//div[text()='로그아웃']")))
        # WebDriverWait(self.driver, 20).until(EC.element_to_be_clickable((By.XPATH,
        #                                                                  "//*[@id='react-root']/section/nav/div[2]/div/div/div[3]/div/div[6]/div[2]/div[2]/div[2]/div[2] | //*[@id='react-root']/div/div/section/nav/div[2]/div/div/div[3]/div/div[6]/div[2]/div[2]/div[2]/div[2]")))
    except Exception as e:
        self.logger.error(f"maybe this is app version")
        try:
            WebDriverWait(self.driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//div[@class='_abm0']/*[name()='svg'][@aria-label='옵션']"))).click()
        except Exception as e:
            self.logger.error(f"weird account")
            return False
        else:
            self.driver.find_element(By.XPATH, "//button[text()='로그아웃']").click()
            return True
    else:
        self.driver.find_element(By.XPATH, "//div[text()='로그아웃']").click()
        return True