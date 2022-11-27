import pymongo
from pymongo.server_api import ServerApi

# client = pymongo.MongoClient("mongodb+srv://datacast:AZJNzYMVYCiL1WQx@kjy.egbmu.mongodb.net/?retryWrites=true&w=majority")
client = pymongo.MongoClient(host="mongodb+srv://kjy.egbmu.mongodb.net/?retryWrites=true&w=majority", port=None, username="datacast", password="AZJNzYMVYCiL1WQx",unicode_decode_error_handler='ignore',authSource="admin", authMechanism="SCRAM-SHA-1")
service_instagram_db = client["service_instagram"]
test_collection = service_instagram_db["user_checkpoint"]
s = test_collection.find({}).limit(10)
print(list(s))
