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

class NasDB:
    def __init__(self,db_name=None):
        self.db_name = db_name
        self.conn = pymongo.MongoClient("61.98.230.194:27020",
                    username="datacast",
                    password="amdc7025!",
                    authSource="admin",
                    #authMechanism="SCRAM-SHA-1",
                    directConnection = True,
                    unicode_decode_error_handler='ignore')
        self.db = self.conn[self.db_name] if db_name else None
        self.account_collection = self.conn['account']['account']
        FORMAT = '%(module)s.%(funcName)s - %(message)s - %(levelname)s - %(asctime)s'
        logging.basicConfig(format=FORMAT)
        logger = logging.getLogger(__name__)
        if logger.hasHandlers():
            # Logger is already configured, remove all handlers
            logger.handlers = []
        logger.setLevel(logging.INFO)
        self.logger = logger

class InstaDB:
    def __init__(self,db_name=None):
        self.db_name = db_name
        self.conn = pymongo.MongoClient("218.153.187.100:27017", directConnection=True, username="datacast", password="amdc2580!", authSource="admin", authMechanism="SCRAM-SHA-1", unicode_decode_error_handler='ignore')
        self.db = self.conn[self.db_name] if db_name else None
        self.account_collection = self.conn['account']['account']
        self.bandncast_account_collection = self.conn["bandncast"]["account"]
        FORMAT = '%(module)s.%(funcName)s - %(message)s - %(levelname)s - %(asctime)s'
        logging.basicConfig(format=FORMAT)
        logger = logging.getLogger(__name__)
        if logger.hasHandlers():
            # Logger is already configured, remove all handlers
            logger.handlers = []
        logger.setLevel(logging.INFO)
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
        FORMAT = 'INSTAGRAM_TARGETING_BOTs %(asctime)s - %(levelname)s - %(name)s - %(module)s.%(funcName)s - %(message)s'
        logging.basicConfig(format=FORMAT)
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        self.logger = logger

    def set_client(self, client_name):
        self.client_name = client_name
        self.client_info_doc = self.collection.find_one({"client_name": client_name})
        self._id = self.client_info_doc["_id"]
        self.password = self.client_info_doc["password"]
        self.hashtag_usage = self.client_info_doc["usage"]["hashtag"]
        self.hashtag_limit = self.client_info_doc["limit"]["hashtag"]
        self.search_usage = self.client_info_doc["usage"]["search"]
        self.search_limit = self.client_info_doc["limit"]["search"]
        self.dm_usage = self.client_info_doc["usage"]["dm"]
        self.dm_limit = self.client_info_doc["limit"]["dm"]
        self.subscription_start = self.client_info_doc["subscription"]["start"]
        self.subscription_end = self.client_info_doc["subscription"]["end"]
        self.concurrency_usage = self.client_info_doc["usage"]["concurrency"]
        self.concurrency_limit = self.client_info_doc["limit"]["concurrency"]

    @property
    def document(self):
        return self.collection.find_one({"_id": self._id})
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

    def dm_extract(self):
        self.collection.update_one({"_id": self._id}, {"$inc": {"usage.dm": 1}})

    def search_extract(self):
        self.collection.update_one({"_id": self._id}, {"$inc": {"usage.search": 1}})

class InstaAccount(InstaDB):
    def __init__(self,client_name=None,channel_name= None,username= None,account_crawl_max_num =200):
        super().__init__(db_name="account")
        self.collection = self.db["account"]
        self.account_checkpoint_collection = self.db["account_checkpoint"]
        self.checkpoint_collection = self.db["checkpoint"]
        self.username = username
        self.client_name = client_name
        self.channel_name = channel_name
        self.account_crawl_max_num = account_crawl_max_num
        self.account_crawl_num = 0
        FORMAT = 'INSTAGRAM_TARGETING_BOTs %(asctime)s - %(levelname)s - %(name)s - %(module)s.%(funcName)s - %(message)s'
        logging.basicConfig(format=FORMAT)
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        self.logger = logger
        self.dm_limit = 10

    def select_user_and_update_status_to_login(self, username=None):
        ###login 을 위해 따로 선택할 계정이 없는 경우
        self.logger.debug(
            f"db:{self.db_name}/collection:{self.collection.name}/client_name:{self.client_name}/channel_name:{self.channel_name}")
        if username == None:
            if self.client_name != "admin_test":
                filter_raw = {
                    "mobile_session": True,
                    "session": {"$exists": 1},
                    "status": "available",
                    "client_name": self.client_name,
                    "channel": self.channel_name
                }
            else:
                filter_raw = {
                    "mobile_session": True,
                    "session": {"$exists": 1},
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
            if self.client_name != "admin_test":
                filter_raw = {
                    "mobile_session": True,
                    "session": {"$exists": 1},
                    "client_name": self.client_name,
                    "username": username,
                    "status": "available",
                    "channel": self.channel_name
                }
            else:
                filter_raw = {
                    "mobile_session": True,
                    "session": {"$exists": 1},
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

    def select_all_cookie_user(self,username=None, max_messages_per_day=None):
        if not max_messages_per_day:
            max_messages_per_day = 5
        projection = {
                    "_id": 1,
                    "username": 1,
                    "channel": 1,
                    "client_name": 1,
                    "last_login": 1,
                    "limit": 1,
                    "password": 1,
                    "status": 1,
                    "usage": 1,
                    "device_settings":1,
                    "session.csrftoken": 1,
                    "session.ds_user_id": 1,
                    "session.mid": 1,
                    "session.rur":1,
                    "session.sessionid":1,
                    "timing_value":1,
                    "user_agent":1,
                    "uuids":1,
                    "mobile_session":1,
                    "checkpoint":1
                }
        ###login 을 위해 따로 선택할 계정이 없는 경우
        self.logger.debug(f"db:{self.db_name}/collection:{self.collection.name}/client_name:{self.client_name}/channel_name:{self.channel_name}")
        if username == None:
            if self.client_name != "admin":
                filter_raw = {
                "session" : {"$exists":1},
                "mobile_session" : True,
                "status": "available",
                "client_name": self.client_name,
                "channel": self.channel_name,
                "checkpoint.total.messages": {"$lt": max_messages_per_day}
                }
                filter_plus = {
                "session" : {"$exists":1},
                "mobile_session" : True,
                "status": "available",
                "client_name": self.client_name,
                "channel": self.channel_name,
                "checkpoint": {"$exists": False}
                }
            else:
                filter_raw = {
                    "mobile_session": True,
                    "session": {"$exists": 1},
                    "status": "available",
                    "channel": self.channel_name,
                    "checkpoint.total.messages": {"$lt": max_messages_per_day}
                }
                filter_plus = {
                    "mobile_session": True,
                    "session": {"$exists": 1},
                    "status": "available",
                    "channel": self.channel_name,
                    "checkpoint": {"$exists": False}
                }
            self.logger.debug(f"filter_raw:{filter_raw}")
            available_account_list = list(self.account_checkpoint_collection.find({"$or":[filter_raw,filter_plus]}, projection, sort=[('last_login', 1)]))

        ##login 을 위해 따로 선택할 계정이 있는 경우
        else:
            if self.client_name != "admin":
                filter_raw = {
                    "mobile_session": True,
                    "session": {"$exists": 1},
                    "client_name": self.client_name,
                    "username": username,
                    "status": "available",
                    "channel": self.channel_name,
                    "checkpoint.total.messages": {"$lt": max_messages_per_day}
                },
                filter_plus = {
                    "session": {"$exists": 1},
                    "mobile_session": True,
                    "status": "available",
                    "username": username,
                    "client_name": self.client_name,
                    "channel": self.channel_name,
                    "checkpoint": {"$exists": False}
                }
            else:
                filter_raw = {
                    "mobile_session": True,
                    "session": {"$exists": 1},
                    "username": username,
                    "status": "available",
                    "channel": self.channel_name,
                    "checkpoint.total.messages": {"$lt": max_messages_per_day},
                }
                filter_plus = {
                    "mobile_session": True,
                    "session": {"$exists": 1},
                    "username": username,
                    "status": "available",
                    "channel": self.channel_name,
                    "checkpoint": {"$exists": False}
                }
            self.logger.debug(f"filter_raw:{filter_raw}")
            available_account_list = list(self.account_checkpoint_collection.find({"$or":[filter_raw,filter_plus]}, projection))

        return available_account_list

    def select_cookie_user_many_v1(self, username=None, max_messages_per_day=None):
        projection = {
            "_id": 1,
            "username": 1,
            "channel": 1,
            "client_name": 1,
            "last_login": 1,
            "limit": 1,
            "password": 1,
            "status": 1,
            "usage": 1,
            "device_settings": 1,
            "session.csrftoken": 1,
            "session.ds_user_id": 1,
            "session.mid": 1,
            "session.rur": 1,
            "session.sessionid": 1,
            "timing_value": 1,
            "user_agent": 1,
            "uuids": 1
        }

        if self.client_name != "admin":
            filter_raw = {
                "session": {"$exists": 1},
                "mobile_session": True,
                "status": "available",
                "client_name": self.client_name,
                "channel": self.channel_name,
                "checkpoint.total.messages": {"$lt": max_messages_per_day}
            }
            filter_plus = {
                "session": {"$exists": 1},
                "mobile_session": True,
                "status": "available",
                "client_name": self.client_name,
                "channel": self.channel_name,
                "checkpoint": {"$exists": False}
            }
        else:
            filter_raw = {
                "mobile_session": True,
                "session": {"$exists": 1},
                "status": "available",
                "channel": self.channel_name,
                "checkpoint.total.messages": {"$lt": max_messages_per_day}
            }
            filter_plus = {
                "mobile_session": True,
                "session": {"$exists": 1},
                "status": "available",
                "channel": self.channel_name,
                "checkpoint": {"$exists": False}
            }
        if username:
            filter_raw.update(username=username)
            filter_plus.update(username=username)

        if self.client_name:
            filter_raw.update(client_name=self.client_name)
            filter_plus.update(client_name=self.client_name)

        self.logger.debug(f"filter_raw:{filter_raw}")
        available_account = self.account_collection.find({"$or": [filter_raw, filter_plus]}, projection,
                                                                        sort=[('last_login', 1)])
        available_account = list(available_account)
        if available_account is None:
            return None
        return available_account
    def select_cookie_user_v1(self, username=None, max_messages_per_day=None):
        if not max_messages_per_day:
            max_messages_per_day = 5
        projection = {
            "_id": 1,
            "username": 1,
            "channel": 1,
            "client_name": 1,
            "last_login": 1,
            "limit": 1,
            "password": 1,
            "status": 1,
            "usage": 1,
            "device_settings": 1,
            "session.csrftoken": 1,
            "session.ds_user_id": 1,
            "session.mid": 1,
            "session.rur": 1,
            "session.sessionid": 1,
            "timing_value": 1,
            "user_agent": 1,
            "uuids": 1
        }

        if self.client_name != "admin":
            filter_checkpoint_date = {
            "session" : {"$exists":1},
            "mobile_session" : True,
            "status": "available",
            "client_name": self.client_name,
            "channel": self.channel_name,
            "checkpoint.start_time": {"$lte": datetime.now()- timedelta(days=14)}
            }

            filter_raw = {
            "session" : {"$exists":1},
            "mobile_session" : True,
            "status": "available",
            "client_name": self.client_name,
            "channel": self.channel_name,
            "checkpoint.total.messages": {"$lt": max_messages_per_day}
            }

            filter_plus = {
            "session" : {"$exists":1},
            "mobile_session" : True,
            "status": "available",
            "client_name": self.client_name,
            "channel": self.channel_name,
            "checkpoint": {"$exists": False}
            }

        else:
            filter_checkpoint_date = {
            "session" : {"$exists":1},
            "mobile_session" : True,
            "status": "available",
            "channel": self.channel_name,
            "checkpoint.start_time": {"$lte": datetime.now()- timedelta(days=14)}
            }

            filter_raw = {
                "mobile_session": True,
                "session": {"$exists": 1},
                "status": "available",
                "channel": self.channel_name,
                "checkpoint.total.messages": {"$lt": max_messages_per_day}
            }
            filter_plus = {
                "mobile_session": True,
                "session": {"$exists": 1},
                "status": "available",
                "channel": self.channel_name,
                "checkpoint": {"$exists": False}
            }
        if username:
            filter_raw.update(username=username)
            filter_plus.update(username=username)
            filter_checkpoint_date.update(username=username)

        if self.client_name:
            filter_raw.update(client_name=self.client_name)
            filter_plus.update(client_name=self.client_name)
            filter_checkpoint_date.update(client_name=self.client_name)
        self.logger.debug(f"filter_raw:{filter_raw}")
        available_account = self.account_collection.find_one_and_update(filter={"$or": [filter_raw, filter_plus, filter_checkpoint_date]}, update={"$set":{"status":"login","last_login":datetime.now()}}, projection=projection ,sort=[('last_login', 1)])

        if available_account is not None:
            self.username = available_account["username"]
        else:
            self.logger.debug(f"available_account is None")
            return None
        return available_account


    def find_account(self, total_required_account:int):
        projection = {"username": 1, "_id":0}
        available_account = self.account_collection.find(filter={"status": "available"},  projection=projection, sort=[('last_login', 1)]).limit(total_required_account)
        return available_account

    def select_and_update_user(self, username=None):
        filter = {"status":"available"}
        if username:
            filter.update(username=username)
        projection = {"username": 1,
                      "password":1,
                      "_id": 0}
        available_account = self.account_collection.find_one_and_update(filter=filter,
                                                                        update={"$set": {"status": "login", "last_login": datetime.now()}},
                                                                        projection=projection,
                                                                        sort=[('last_login', 1)]
                                                                        )

        return available_account
    def select_cookie_user_v2(self, username=None, max_messages_per_day=None):
        if not max_messages_per_day:
            max_messages_per_day = 5
        projection = {
            "_id": 1,
            "username": 1,
            "channel": 1,
            "client_name": 1,
            "last_login": 1,
            "limit": 1,
            "password": 1,
            "status": 1,
            "usage": 1,
            "device_settings": 1,
            "session.csrftoken": 1,
            "session.ds_user_id": 1,
            "session.mid": 1,
            "session.rur": 1,
            "session.sessionid": 1,
            "timing_value": 1,
            "user_agent": 1,
            "uuids": 1
        }

        if self.client_name != "admin":
            filter_plus = {
            "session" : {"$exists":1},
            "mobile_session" : True,
            "status": "available",
            "client_name": self.client_name,
            "channel": self.channel_name,
            "checkpoint": {"$exists": False}
            }

        else:
            filter_plus = {
                "mobile_session": True,
                "session": {"$exists": 1},
                "status": "available",
                "channel": self.channel_name,
                "checkpoint": {"$exists": False}
            }
        if username:

            filter_plus.update(username=username)


        if self.client_name:
            filter_plus.update(client_name=self.client_name)

        # self.logger.info(f"filter_raw:{filter_plus}")
        available_account = self.account_collection.find_one_and_update(filter={"$or": [filter_plus]}, update={"$set":{"status":"login","last_login":datetime.now()}}, projection=projection, sort=[('last_login', -1)])

        if available_account is not None:
            self.username = available_account["username"]
        else:
            self.logger.debug(f"available_account is None")
            return None
        return available_account
    def select_cookie_user(self,username=None, max_messages_per_day=None):
        if not max_messages_per_day:
            max_messages_per_day = 5
        projection = {
                    "_id": 1,
                    "username": 1,
                    "channel": 1,
                    "client_name": 1,
                    "last_login": 1,
                    "limit": 1,
                    "password": 1,
                    "status": 1,
                    "usage": 1,
                    "device_settings":1,
                    "session.csrftoken": 1,
                    "session.ds_user_id": 1,
                    "session.mid": 1,
                    "session.rur":1,
                    "session.sessionid":1,
                    "timing_value":1,
                    "user_agent":1,
                    "uuids":1,
                    "mobile_session":1
                }
        ###login 을 위해 따로 선택할 계정이 없는 경우
        self.logger.debug(f"db:{self.db_name}/collection:{self.collection.name}/client_name:{self.client_name}/channel_name:{self.channel_name}")


        filter_raw = {
            "mobile_session": True,
            "session": {"$exists": 1},
            "status": "available",
            "channel": self.channel_name,
            "checkpoint.total.messages": {"$lt": max_messages_per_day}
        }

        filter_plus = {
            "mobile_session": True,
            "session": {"$exists": 1},
            "status": "available",
            "channel": self.channel_name,
            "checkpoint": {"$exists": False}
        }
        if username:
            filter_raw.update(username=username)
            filter_plus.update(username=username)

        if self.client_name:
            filter_raw.update(client_name=self.client_name)
            filter_plus.update(client_name=self.client_name)

        self.logger.debug(f"filter_raw:{filter_raw}")
        available_account = self.account_checkpoint_collection.find_one({"$or":[filter_raw,filter_plus]}, projection, sort=[('last_login', 1)])

        if available_account is not None:
            self.username = available_account["username"]
        else:
            self.logger.debug(f"available_account is None")
            return None
        return available_account

    def logout(self):
        ##logout 하는 경우에는 계정의 상태를 available 로 변경하고 last_login 을 현재시간으로 업데이트 시켜준다.

        self.update_available()

    def update_available(self,username=None):
        ##logout 하는 경우에는 계정의 상태를 available 로 변경하고 last_login 을 현재시간으로 업데이트 시켜준다.
        if username:
            self.username = username
        update_raw = {"username": self.username, "channel": self.channel_name}
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
        update_raw = {"username": self.username}
        self.logger.debug(f"db:{self.db_name}/collection:{self.collection.name}/update_raw:{update_raw}")
        self.collection.update_one(update_raw,{"$set":{"status":"unavailable"}})

