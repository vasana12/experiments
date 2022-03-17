import hashlib
import hmac
import json
try:
    from json.decoder import JSONDecodeError
except ImportError:
    JSONDecodeError = ValueError
import six.moves.urllib as urllib
import logging
import requests
import requests.utils
from db import m_instagram
from session_save.setting import config
from session_save.setting.botAccount_setting_db import read_account_setting_info_from_db, save_uuid_and_session_info, update_account_unavailable

insta_db = m_instagram.InstaDB(db_name="account")
account_collection = insta_db.account_collection


class loginSession():
    def __init__(self,username, password, proxy=None, session= None):
        self.username =username
        self.password =password
        self.setting_info = read_account_setting_info_from_db(username, password)
        self.session = requests.Session() if not session else session
        FORMAT = '%(module)s.%(funcName)s - %(message)s - %(levelname)s - %(asctime)s'
        logging.basicConfig(format=FORMAT)
        logger = logging.getLogger(__name__)
        if logger.hasHandlers():
            # Logger is already configured, remove all handlers
            logger.handlers = []
        logger.setLevel(logging.INFO)
        self.logger = logger
        host = "texas1.thesocialproxy.com"
        port = "10000"
        mobile_proxy_username = "5rfpjo4evhm0c8dx"
        mobile_proxy_password = "ihzoneqam4p3vt2b"
        username = 'sp22064497'
        password = 'amdc2580!'
        self.last_response = None
        self.last_json = None
        self.proxy = f"http://{config.PROXY_USER}:{config.PROXY_USER}@{config.PROXY_HOST}:{config.PROXY_PORT}" if proxy == None else proxy
        self.set_proxy()
        self.session.headers.update(config.REQUEST_HEADERS)
        self.session.headers.update({"User-Agent": self.setting_info["user_agent"]})


    @staticmethod
    def generate_signature(data):
        body = (
            hmac.new(
                config.IG_SIG_KEY.encode("utf-8"), data.encode("utf-8"), hashlib.sha256
            ).hexdigest()
            + "."
            + urllib.parse.quote(data)
        )
        signature = "signed_body={body}&ig_sig_key_version={sig_key}"

        return signature.format(sig_key=config.SIG_KEY_VERSION, body=body)

    def set_proxy(self):
        if getattr(self, "proxy", None):
            parsed = urllib.parse.urlparse(self.proxy)
            scheme = "http://" if not parsed.scheme else ""
            self.session.proxies["http"] = scheme + self.proxy
            self.session.proxies["https"] = scheme + self.proxy

    def delete_credentials(self):
        pass

    def get_prefill_candidates(self):
        data = {
            "android_device_id": self.setting_info["uuids"]["device_id"],
            "phone_id": self.setting_info["uuids"]["phone_id"],
            "usages": '["account_recovery_omnibox"]',
            "device_id": self.setting_info["uuids"]["device_id"],
        }
        data = json.dumps(data)
        return self.send_request(f"{config.API_URL}accounts/get_prefill_candidates/", post=data,with_signature=True)

    @property
    def cookie_dict(self):
        return self.session.cookies.get_dict()
    @property
    def token(self):
        return self.cookie_dict.get("csrftoken")



    def login_success(self):
        setting_info = read_account_setting_info_from_db(self.username, self.password)
        cookie = requests.utils.dict_from_cookiejar(self.session.cookies)
        setting_info["username"], setting_info["password"], setting_info["cookie"] = self.username, self.password, cookie
        self.logger.info(f"{self.username}/{self.password} success - > account collection")
        msg = f"SETTING INFO : COOKIE \n- {cookie} - " \
              f"TIMING, DEVICE and ...\n- user-agent={setting_info['user_agent']}\n- phone_id={setting_info['uuids']['phone_id']}\n- " \
              f"uuid={setting_info['uuids']['uuid']}\n- client_session_id={setting_info['uuids']['client_session_id']}\n- device_id={setting_info['uuids']['device_id']}"
        self.logger.debug(msg)
        save_uuid_and_session_info(setting_info)
        return True

    def login_failed(self):
        self.logger.info(f"request login failed {self.username}/{self.password} update unavailable")
        update_account_unavailable(username=self.username)

    def login(self):
        self.logger.info(f"login_trial")
        data = json.dumps({
            "jazoest": "22264",
            "country_codes": '[{"country_code":"1","source":["default"]}]',
            "phone_id": self.setting_info["uuids"]["phone_id"],
            "_csrftoken": self.token,
            "username": self.username,
            "adid": "",
            "guid": self.setting_info["uuids"]["uuid"],
            "device_id": self.setting_info["uuids"]["device_id"],
            "google_tokens": "[]",
            "password": self.password,
            # "enc_password:" "#PWD_INSTAGRAM:4:TIME:ENCRYPTED_PASSWORD"
            "login_attempt_count": "0",
        })
        response = self.send_request(f"{config.API_URL}accounts/login/", post=data, with_signature=True)

        if response:
            return self.login_success()
        else:
            self.login_failed()
            return False

    def send_request(self, url, post, with_signature, extra_sig=None,timeout=30,waiting_429=None):
        method = "POST" if post else "GET"
        if post is not None:  # POST
            if with_signature:
                post = self.generate_signature(post)  #
                if extra_sig is not None and extra_sig != []:
                    post += "&".join(extra_sig)
            try:
                response = self.session.post(url, data=post,timeout=timeout)
            except Exception as e:
                self.logger.debug(f"error:{e}")
                return False
        else:
            response = self.session.get(url,timeout=timeout)
            return response

        self.last_response = response
        self.logger.info(f"{method} to endpoint:{url} returned response: {response.status_code}")
        if response.status_code == 200:
            try:
                self.last_json = json.loads(response.text)
                return True
            except JSONDecodeError:
                self.logger.debug(f"response.status_code - {response.status_code}:JSONDecodeError")
                return False
        else:
            self.logger.debug(f"Responsecode indicated error; returned response : {response.status_code} response content: {response.content[0:100]}")
            return False



