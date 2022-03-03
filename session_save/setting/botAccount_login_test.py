import hashlib
import hmac
import json
import time

import six.moves.urllib as urllib
from datetime import datetime
from datetime import timedelta
import logging
import requests
from db import m_instagram
from session_save.setting import config
from session_save.setting.botAccount_setting_read import read_account_setting_info_from_db
from session_save.util import generate_uuid


insta_db = m_instagram.InstaDB(db_name="account")
account_collection = insta_db.account_collection

FORMAT = 'INSTAGRAM_TARGETING_BOTs %(asctime)s - %(levelname)s - %(name)s - %(module)s.%(funcName)s - %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


JIN_INSTAGRAM = m_instagram.InstaDB(db_name="instagram_analysis").db
JIN_ACCOUNT = JIN_INSTAGRAM["account"]

SERVICE_INSTAGRAM = m_instagram.InstaDB(db_name="service_instagram").db
INSTA_ACCOUNT_OBJ = m_instagram.InstaAccount(client_name="admin", channel_name="instagram").db
ACCOUNT_COLLECTION = INSTA_ACCOUNT_OBJ['account']
BAND_ACCOUNT, HASHTAG_AND_USER, PROJECT_COLLECTION, ITEM_HASHTAG_COLLECTION, ITEM_USER_COLLECTION, ITEM_LOCATION_COLLECTION, INFO_COLLECTION, TASK_COLLECTION, POST_COLLECTION, SEARCH_COLLECTION, SETTING_COLLECTION = \
    SERVICE_INSTAGRAM["account_instagram"], SERVICE_INSTAGRAM["hashtag_and_user"], SERVICE_INSTAGRAM["project"], SERVICE_INSTAGRAM["hashtag"], \
    SERVICE_INSTAGRAM["user"], SERVICE_INSTAGRAM["location"], SERVICE_INSTAGRAM["info"], SERVICE_INSTAGRAM["task"], \
    SERVICE_INSTAGRAM["post"], SERVICE_INSTAGRAM["search"], SERVICE_INSTAGRAM["setting"]

tmp = "http://customer-yxha19913701-asn-9158-sessid-TnHj-sesstime-30:ywiB*20dC@residential.ipb.cloud:7777"

class loginSession():
    def __init__(self,username, password, session= None):
        self.username =username
        self.password =password
        self.setting_info = read_account_setting_info_from_db(username, password)
        self.session = requests.Session() if not session else session
        host = "texas1.thesocialproxy.com"
        port = "10000"
        mobile_proxy_username = "5rfpjo4evhm0c8dx"
        mobile_proxy_password = "ihzoneqam4p3vt2b"
        username = 'sp22064497'
        password = 'amdc2580!'
        proxy = tmp

        self.proxy = proxy
        # self.proxy = f"http://{config.PROXY_USER}:{config.PROXY_USER}@{config.PROXY_HOST}:{config.PROXY_PORT}"
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

    def get_prefill_candidates(self):
        data = {
            "android_device_id": self.setting_info["uuids"]["device_id"],
            "phone_id": self.setting_info["uuids"]["phone_id"],
            "usages": '["account_recovery_omnibox"]',
            "device_id": self.setting_info["uuids"]["device_id"],
        }
        print(data)
        data = json.dumps(data)
        return self.send_request(f"{config.API_URL}accounts/get_prefill_candidates/", post=data,with_signature=True)

    @property
    def cookie_dict(self):
        return self.session.cookies.get_dict()
    @property
    def token(self):
        return self.cookie_dict["csrftoken"]

    def login(self):
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
        return response

    def send_request(self, url, post, with_signature,extra_sig=None):
        if post is not None:  # POST
            if with_signature:
                post = self.generate_signature(post)  #
                if extra_sig is not None and extra_sig != []:
                    post += "&".join(extra_sig)

            print(self.session.proxies)
            response = self.session.post(url, data=post)
            print(self.session.cookies.get_dict())
            print(response.text, response.status_code)
            return response
        else:
            response = self.session.post(url, data=post)
# #
# login_session = loginSession(username="alenaromanova1790", password="FZbjLE2QcS")
# login_session.get_prefill_candidates()
# time.sleep(1)
# response = login_session.login()
# print(response, response.text)


