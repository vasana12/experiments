from db import m_instagram

db_conn = m_instagram.InstaDB().conn

username = "faker"
user_doc = db_conn["service_instagram"]["hashtag_and_user_search"].find_one({"username": username}, {"_id": 1, "userid": 1})

if user_doc and "userid" in user_doc.keys() and user_doc["userid"] is not None:
    print(user_doc)
