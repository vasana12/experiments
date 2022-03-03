import pymongo
from datetime import datetime, timedelta
from bson import ObjectId
import certifi
import logging
ca = certifi.where()
# 로그 생성
# 로그 생성


class NoFoundException(Exception):
    def __init__(self, msg):
        self.msg = msg
    def __str__(self):
        return self.msg

class InstaDB:
    def __init__(self,db_name=None):
        self.db_name = db_name
        self.conn = pymongo.MongoClient("mongodb+srv://datacast:amdc7025!@cluster0.egbmu.mongodb.net/admin?retryWrites=true&w=majority", tlsCAFile=ca,unicode_decode_error_handler='ignore')
        self.db = self.conn[self.db_name] if db_name else None
        self.account_collection = self.conn['account']['account']
        FORMAT = 'INSTAGRAM_TARGETING_BOTs %(asctime)s - %(levelname)s - %(name)s - %(funcName)s - %(message)s'
        logging.basicConfig(format=FORMAT)
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.DEBUG)
        self.logger = logger

    def update_batch_next_page_info(self,batch_id,instagram_crawl_instance):
        self.conn["service_supertag"]["batch"].update_one({"_id": ObjectId(batch_id)}, {"$set":
            {
                "next_page_token_info":
                    {
                        "next_page": instagram_crawl_instance.next_page,
                        "next_max_id": instagram_crawl_instance.next_max_id
                    }
            }
        }
                                                                           )
    def find_user_by_username(self,username):
        count = self.conn[self.db_name]["content"].find({"usernmae":username}).count()
        return count
    def update_batch_login_max_retry_error(self,batch_id):
        self.conn[self.db_name]["batch"].update_one({"_id": ObjectId(batch_id)}, {
            "$set": {"status": "login_max_retry_error"}})

    def update_batch_login_no_more_account_error(self,batch_id):
        self.conn[self.db_name]["batch"].update_one({"_id": ObjectId(batch_id)},{
            "$set": {"status": "login_no_more_account_error"}})

class InstaBotClient(InstaDB):
    def __init__(self,client_name=None,channel_name=None):
        super().__init__(db_name="service_instagram")
        self.client_name = client_name
        self.password = None
        self.collection = self.db["client"]
        self.status = None
        self._id = None
        self.client_info_doc = None
        self.hashtag_usage = None
        self.hashtag_limit = None
        self.dm_usage = None
        self.dm_limit = None
        self.subscription_start = None
        self.subscription_end = None
        self.concurrency_usage = None
        self.concurrency_limit = None
        FORMAT = 'INSTAGRAM_TARGETING_BOTs %(asctime)s - %(levelname)s - %(name)s - %(funcName)s - %(message)s'
        logging.basicConfig(format=FORMAT)
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.DEBUG)
        self.logger = logger

    def set_client(self, client_name):
        self.client_name = client_name
        self.client_info_doc = self.collection.find_one({"client_name": client_name})
        self._id = self.client_info_doc["_id"]
        self.password = self.client_info_doc["password"]
        self.hashtag_usage = self.client_info_doc["usage"]["hashtag"]
        self.hashtag_limit = self.client_info_doc["limit"]["hashtag"]
        self.dm_usage = self.client_info_doc["usage"]["dm"]
        self.dm_limit = self.client_info_doc["limit"]["dm"]
        self.subscription_start = self.client_info_doc["subscription"]["start"]
        self.subscription_end = self.client_info_doc["subscription"]["end"]
        self.concurrency_usage = self.client_info_doc["usage"]["concurrency"]
        self.concurrency_limit = self.client_info_doc["limit"]["concurrency"]

    def login(self):
        self.concurrency_usage = self.concurrency_usage + 1
        self.collection.update_one({"_id": self._id}, {"$set": {"usage.concurrency": self.concurrency_usage}})
        self.logger.debug(f"로그인 후 CONCURRENCY:{self.concurrency_usage}")
    def logout(self):
        self.concurrency_usage = self.concurrency_usage - 1
        self.collection.update_one({"_id": self._id}, {"$set": {"usage.concurrency": self.concurrency_usage}})
        self.logger.debug(f"로그아웃 후 CONCURRENCY:{self.concurrency_usage}")

    def hashtag_extract(self):
        self.collection.update_one({"_id": self._id}, {"$inc": {"usage.hashtag": 1}})

class InstaAccount(InstaDB):
    def __init__(self,client_name=None,channel_name= None,username= None,account_crawl_max_num =200):
        super().__init__(db_name="account")
        self.collection = self.db["account"]
        self.username = username
        self.client_name = client_name
        self.channel_name = channel_name
        self.account_crawl_max_num = account_crawl_max_num
        self.account_crawl_num = 0
        FORMAT = 'INSTAGRAM_TARGETING_BOTs %(asctime)s - %(levelname)s - %(name)s - %(funcName)s - %(message)s'
        logging.basicConfig(format=FORMAT)
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        self.logger = logger
        self.dm_limit = 10
    def select_user_and_update_status_to_login(self,username=None):
        ###login 을 위해 따로 선택할 계정이 없는 경우
        self.logger.debug(f"db:{self.db_name}/collection:{self.collection.name}/client_name:{self.client_name}/channel_name:{self.channel_name}")
        if username == None:
            if self.client_name != "admin":
                filter_raw = {
                "status": "available",
                "client_name": self.client_name,
                "channel": self.channel_name
                }
            else:
                filter_raw = {
                    "status": "available",
                    "channel": self.channel_name
                }
            self.logger.debug(f"filter_raw:{filter_raw}")
            available_account = self.collection.find_one_and_update(
                filter_raw,
                {
                    "$set":
                        {
                            "status": "login",
                            "last_login": datetime.now()
                        }
                },
                sort=[('last_login', 1)]
            )
        ##login 을 위해 따로 선택할 계정이 있는 경우
        else:
            if self.client_name != "admin":
                filter_raw = {
                    "client_name": self.client_name,
                    "username": username,
                    "status": "available",
                    "channel": self.channel_name
                }
            else:
                filter_raw = {
                    "username": username,
                    "status": "available",
                    "channel": self.channel_name
                }
            self.logger.debug(f"filter_raw:{filter_raw}")
            available_account = self.collection.find_one_and_update(
                filter_raw,
                {
                    "$set": {
                        "status": "login",
                          "last_login": datetime.now()
                    }
                })

        self.logger.info(f"available_account:{available_account}")

        if available_account is not None:
            self.username = available_account["username"]
        else:
            self.logger.debug(f"available_account is None")
            return None
        return available_account
    def update_dm_usage_0(self):
        two_days_ago = datetime.now()-timedelta(days=2)
        self.collection.update_many({"last_login":{"$lte":two_days_ago}},{"$set":{"usage.dm": 0}})
    def select_user_and_update_status_to_login_dm(self,username=None):
        ###login 을 위해 따로 선택할 계정이 없는 경우
        self.logger.debug(f"db:{self.db_name}/collection:{self.collection.name}/client_name:{self.client_name}/channel_name:{self.channel_name}")
        if username == None:
            if self.client_name != "admin":
                filter_raw = {
                "status": "available",
                "client_name": self.client_name,
                "channel": self.channel_name,
                "usage.dm": {"$lte":self.dm_limit}
                }
            else:
                filter_raw = {
                    "status": "available",
                    "channel": self.channel_name,
                    "usage.dm": {"$lte": self.dm_limit}
                }
            self.logger.debug(f"filter_raw:{filter_raw}")
            available_account = self.collection.find_one_and_update(
                filter_raw,
                {
                    "$set":
                        {
                            "status": "login",
                            "last_login": datetime.now()
                        }
                },
                sort=[('last_login', 1)]
            )
        ##login 을 위해 따로 선택할 계정이 있는 경우
        else:
            if self.client_name != "admin":
                filter_raw = {
                    "client_name": self.client_name,
                    "username": username,
                    "status": "available",
                    "channel": self.channel_name,
                    "usage.dm": {"$lte": self.dm_limit}
                }
            else:
                filter_raw = {
                    "username": username,
                    "status": "available",
                    "channel": self.channel_name,
                    "usage.dm": {"$lte": self.dm_limit}
                }
            self.logger.debug(f"filter_raw:{filter_raw}")
            available_account = self.collection.find_one_and_update(
                filter_raw,
                {
                    "$set": {
                        "status": "login",
                          "last_login": datetime.now()
                    }
                })

        self.logger.info(f"available_account:{available_account}")

        if available_account is not None:
            self.username = available_account["username"]
        else:
            self.logger.debug(f"available_account is None")
            return None
        return available_account
    def load_cookie_user_and_update_status_to_login_dm(self,username=None):
        ###login 을 위해 따로 선택할 계정이 없는 경우
        self.logger.debug(f"db:{self.db_name}/collection:{self.collection.name}/client_name:{self.client_name}/channel_name:{self.channel_name}")
        if username == None:
            if self.client_name != "admin":
                filter_raw = {
                "cookie" : {"$exists":1},
                "status": "available",
                "client_name": self.client_name,
                "channel": self.channel_name,
                "usage.dm": {"$lte":self.dm_limit}
                }
            else:
                filter_raw = {
                    "cookie": {"$exists": 1},
                    "status": "available",
                    "channel": self.channel_name,
                    "usage.dm": {"$lte": self.dm_limit}
                }
            self.logger.debug(f"filter_raw:{filter_raw}")
            available_account = self.collection.find_one_and_update(
                filter_raw,
                {
                    "$set":
                        {
                            "status": "login",
                            "last_login": datetime.now()
                        }
                },
                sort=[('last_login', 1)]
            )
        ##login 을 위해 따로 선택할 계정이 있는 경우
        else:
            if self.client_name != "admin":
                filter_raw = {
                    "cookie": {"$exists": 1},
                    "client_name": self.client_name,
                    "username": username,
                    "status": "available",
                    "channel": self.channel_name,
                    "usage.dm": {"$lte": self.dm_limit}
                }
            else:
                filter_raw = {
                    "cookie": {"$exists": 1},
                    "username": username,
                    "status": "available",
                    "channel": self.channel_name,
                    "usage.dm": {"$lte": self.dm_limit}
                }
            self.logger.debug(f"filter_raw:{filter_raw}")
            available_account = self.collection.find_one_and_update(
                filter_raw,
                {
                    "$set": {
                        "status": "login",
                          "last_login": datetime.now()
                    }
                })

        self.logger.info(f"available_account:{available_account}")

        if available_account is not None:
            self.username = available_account["username"]
        else:
            self.logger.debug(f"available_account is None")
            return None
        return available_account
    def logout(self):
        ##logout 하는 경우에는 계정의 상태를 available 로 변경하고 last_login 을 현재시간으로 업데이트 시켜준다.

        self.update_available()

    def update_available(self):
        ##logout 하는 경우에는 계정의 상태를 available 로 변경하고 last_login 을 현재시간으로 업데이트 시켜준다.
        if self.client_name != "admin":
            update_raw = {
                "client_name": self.client_name, "username": self.username, "channel": self.channel_name,
            }
        else:
            update_raw = {
                 "username": self.username, "channel": self.channel_name,
            }
        self.logger.info(f"db:{self.db_name}/collection:{self.collection.name}/update_raw:{update_raw}")
        self.collection.update_one(
            update_raw,
            {
                "$set":{
                    "status":"available",
                    "last_login": datetime.now()
                }
            }
        )

    def update_unavailable(self):
        ##계정을 사용할 수 없는 경우네는 계정의 상태를 unavailable 로 변경한다.
        if self.client_name != "admin":
            update_raw = {
                "client_name": self.client_name, "username": self.username, "channel": self.channel_name,
            }
        else:
            update_raw = {
                 "username": self.username, "channel": self.channel_name,
            }
        self.logger.debug(f"db:{self.db_name}/collection:{self.collection.name}/update_raw:{update_raw}")
        self.collection.update_one(update_raw,{"$set":{"status":"unavailable","last_login": datetime.now()}})

