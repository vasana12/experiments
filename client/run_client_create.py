from datetime import datetime, timedelta
from client.utils.password_generator import generatePassword
from db import m_instagram
db = m_instagram.InstaDB(db_name="service_instagram").db
client_collection = db["client"]

setting_info ={
    "subscription": {
        "start" : datetime.now(),
        "end" : datetime.now()+ timedelta(days=30)
    },
    "limit": {
        "hashtag": 9999999999,
        "dm": 500,
        "search": 500,
        "concurrency": 5
    },
    "usage": {
        "hashtag": 0,
        "dm": 0,
        "search": 0,
        "concurrency": 0
    },
    "group": "test",
    "password" : generatePassword()
}
client_name = "test_baejin_10"
setting_info.update(client_name=client_name)
client_collection.insert_one(setting_info)
