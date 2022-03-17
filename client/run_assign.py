from db import m_instagram
import logging

FORMAT = '%(module)s.%(funcName)s - %(message)s - %(levelname)s - %(asctime)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)
if logger.hasHandlers():
    # Logger is already configured, remove all handlers
    logger.handlers = []
logger.setLevel(logging.INFO)

client_name = "admin_test"
insta_account_obj = m_instagram.InstaAccount()
insta_account_obj.client_name = client_name
insta_account_obj.channel_name = "instagram"
account_collection = insta_account_obj.account_collection

account = insta_account_obj.select_cookie_user_many_v1(username=None)
print(len(account))

for i in range(2,11):
    for account in range(0, 50):
        account_info = insta_account_obj.select_cookie_user_v1(username=None)
        print(account_info)
        account_collection.update_one({"username":account_info.get("username")}, {"$set": {"client_name": f"test_baejin_{i}"}})
    print(f"test_baejin_{i} finish")




