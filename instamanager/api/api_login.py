import json
import os
import random
import time
import traceback

import requests
import requests.utils

from . import config, devices

# ====== SYNC METHODS ====== #


def sync_device_features(self, login=False):
    data = {
        "id": self.uuid,
        "server_config_retrieval": "1",
        "experiments": config.LOGIN_EXPERIMENTS,
    }
    if login is False:
        data["_uuid"] = self.uuid
        data["_uid"] = self.user_id
        data["_csrftoken"] = self.token
    data = json.dumps(data)
    self.last_experiments = time.time()
    return self.send_request(
        "qe/sync/", data, login=login, headers={"X-DEVICE-ID": self.uuid}
    )


def sync_launcher(self, login=False):
    data = {
        "id": self.uuid,
        "server_config_retrieval": "1",
    }
    if login is False:
        data["_uid"] = self.user_id
        data["_uuid"] = self.uuid
        data["_csrftoken"] = self.token
    data = json.dumps(data)
    return self.send_request("launcher/sync/", data, login=login)


def sync_user_features(self):
    data = self.default_data
    data["id"] = self.uuid
    data["experiments"] = config.EXPERIMENTS
    data = json.dumps(data)
    self.last_experiments = time.time()
    return self.send_request("qe/sync/", data, headers={"X-DEVICE-ID": self.uuid})


# "android_device_id":"android-f14b9731e4869eb",
# "phone_id":"b4bd7978-ca2b-4ea0-a728-deb4180bd6ca",
# "usages":"[\"account_recovery_omnibox\"]",
# "_csrftoken":"9LZXBXXOztxNmg3h1r4gNzX5ohoOeBkI",
# "device_id":"70db6a72-2663-48da-96f5-123edff1d458"
def get_prefill_candidates(self, login=False):
    data = {
        "android_device_id": self.device_id,
        "phone_id": self.phone_id,
        "usages": '["account_recovery_omnibox"]',
        "device_id": self.device_id,
    }
    if login is False:
        data["_csrftoken"] = self.token
    data = json.dumps(data)
    return self.send_request("accounts/get_prefill_candidates/", data, login=login)


def get_account_family(self):
    return self.send_request("multiple_accounts/get_account_family/")


def get_zr_token_result(self):
    url = (
        "zr/token/result/?device_id={rank_token}"
        "&token_hash=&custom_device_id={custom_device_id}&fetch_reason=token_expired"
    )
    url = url.format(rank_token=self.device_id, custom_device_id=self.device_id)
    return self.send_request(url)


def banyan(self):
    url = "banyan/banyan/?views=['story_share_sheet','threads_people_picker','group_stories_share_sheet','reshare_share_sheet']"
    return self.send_request(url)


def igtv_browse_feed(self):
    url = "igtv/browse_feed/?prefetch=1"
    return self.send_request(url)


def creatives_ar_class(self):
    data = {
        "_csrftoken": self.token,
        "_uuid": self.uuid,
    }
    data = json.dumps(data)
    return self.send_request("creatives/ar_class/", data)


# ====== LOGIN/PRE FLOWS METHODS ====== #


def pre_login_flow(self):
    self.logger.info("Not yet logged in starting: PRE-LOGIN FLOW!")

    # /api/v1/accounts/get_prefill_candidates
    self.get_prefill_candidates(True)

    # /api/v1/qe/sync (server_config_retrieval)
    self.sync_device_features(True)

    # /api/v1/launcher/sync/ (server_config_retrieval)
    self.sync_launcher(True)

    # /api/v1/accounts/contact_point_prefill/
    self.set_contact_point_prefill("prefill")

    # /api/v1/accounts/get_prefill_candidates/
    # self.get_prefill_candidates(True)

    # /api/v1/accounts/contact_point_prefill/
    # self.set_contact_point_prefill("prefill")

    # /api/v1/qe/sync/ (server_config_retrieval)
    # self.sync_device_features(True)

    # /api/v1/launcher/sync/ (server_config_retrieval)
    # self.sync_launcher(True)


# DO NOT MOVE ANY OF THE ENDPOINTS THEYRE IN THE CORRECT ORDER
def login_flow(self, just_logged_in=False, app_refresh_interval=1800):
    self.last_experiments = time.time()
    self.logger.info("LOGIN FLOW! Just logged-in: {}".format(just_logged_in))
    check_flow = []
    if just_logged_in:
        try:
            pass

        except Exception as e:
            self.logger.error(
                "Exception raised: {}\n{}".format(e, traceback.format_exc())
            )
            return False
    else:
        try:
            pull_to_refresh = random.randint(1, 100) % 2 == 0
            check_flow.append(
                self.get_timeline_feed(
                    options=["is_pull_to_refresh"] if pull_to_refresh is True else []
                )
            )  # Random pull_to_refresh :)
            check_flow.append(
                self.get_reels_tray_feed(
                    reason="pull_to_refresh"
                    if pull_to_refresh is True
                    else "cold_start"
                )
            )

            is_session_expired = (time.time() - self.last_login) > app_refresh_interval

            if is_session_expired:
                self.last_login = time.time()
                self.client_session_id = self.generate_UUID(uuid_type=True)

        except Exception as e:
            self.logger.error(
                "Error loginin, exception raised: {}\n{}".format(
                    e, traceback.format_exc()
                )
            )
            return False

    self.save_uuid_and_cookie()
    return False if False in check_flow else True


# ====== DEVICE / CLIENT_ID / PHONE_ID AND OTHER VALUES (uuids) ====== #


def set_device(self):
    # self.device_settings = devices.DEVICES[self.device]
    # self.user_agent = config.USER_AGENT_BASE.format(**self.device_settings)
    self.device_settings = self.account_setting_info["device_settings"]
    self.user_agent = self.account_setting_info["user_agent"]

def generate_all_uuids(self):
    # self.phone_id = self.generate_UUID(uuid_type=True)
    # self.uuid = self.generate_UUID(uuid_type=True)
    # self.client_session_id = self.generate_UUID(uuid_type=True)
    # self.advertising_id = self.generate_UUID(uuid_type=True)
    # self.device_id = self.generate_device_id(
    #     self.get_seed(self.username, self.password)
    # )
    self.phone_id = self.account_setting_info["uuids"]["phone_id"]
    self.uuid = self.account_setting_info["uuids"]["uuid"]
    self.client_session_id = self.account_setting_info["uuids"]["client_session_id"]
    self.advertising_id = self.account_setting_info["uuids"]["phone_id"]
    self.device_id = self.account_setting_info["uuids"]["phone_id"]

def reinstall_app_simulation(self):
    self.logger.info("Reinstall app simulation, generating new `phone_id`...")
    self.phone_id = self.generate_UUID(uuid_type=True)
    self.save_uuid_and_cookie()
    self.logger.info("New phone_id: {}".format(self.phone_id))


def change_device_simulation(self):
    self.logger.info("Change device simulation")
    self.reinstall_app_simulation()
    self.logger.info("Generating new `android_device_id`...")
    self.device_id = self.generate_device_id(
        self.get_seed(self.generate_UUID(uuid_type=True))
    )
    self.save_uuid_and_cookie()
    self.logger.info("New android_device_id: {}".format(self.device_id))


def load_uuid_and_cookie(self):

    try:
        self.last_login = self.account_setting_info["timing_value"]["last_login"]
        self.last_experiments = self.account_setting_info["timing_value"]["last_experiments"]

        self.logger.info("Loading session cookies")
        self.session.cookies = requests.utils.cookiejar_from_dict(self.account_setting_info["session"])
        self.logger.debug(f"self.session_info['session']:{self.account_setting_info['session']}")

        self.logger.debug("Loading uuids")
        self.phone_id = self.account_setting_info["uuids"]["phone_id"]
        self.uuid = self.account_setting_info["uuids"]["uuid"]
        self.client_session_id = self.account_setting_info["uuids"]["client_session_id"]
        self.advertising_id = self.account_setting_info["uuids"]["advertising_id"]
        self.device_id = self.account_setting_info["uuids"]["device_id"]

        self.device_settings = self.account_setting_info["device_settings"]
        self.user_agent = self.account_setting_info["user_agent"]
    except Exception as e:
        self.logger.error(f"load uuid and cookie error: {e}")
    self.logger.info(f"load uuid and cookie success")
    return True

def save_uuid_and_cookie(self):
    if self.cookie_fname is None:
        fname = "{}_uuid_and_cookie.json".format(self.username)
        self.cookie_fname = os.path.join(self.base_path, fname)

    data = {
        "uuids": {
            "phone_id": self.phone_id,
            "uuid": self.uuid,
            "client_session_id": self.client_session_id,
            "advertising_id": self.advertising_id,
            "device_id": self.device_id,
        },
        "cookie": requests.utils.dict_from_cookiejar(self.session.cookies),
        "timing_value": {
            "last_login": self.last_login,
            "last_experiments": self.last_experiments,
        },
        "device_settings": self.device_settings,
        "user_agent": self.user_agent,
    }
    with open(self.cookie_fname, "w") as f:
        json.dump(data, f)
