import xlsxwriter
from db import m_instagram
import logging
import pandas as pd
FORMAT = '%(module)s.%(funcName)s - %(message)s - %(levelname)s - %(asctime)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)
if logger.hasHandlers():
    # Logger is already configured, remove all handlers
    logger.handlers = []
logger.setLevel(logging.INFO)

client_name = "admin_test"
client_collection = m_instagram.InstaBotClient().collection

insta_account_obj = m_instagram.InstaAccount()
insta_account_obj.client_name = client_name
insta_account_obj.channel_name = "instagram"
account_collection = insta_account_obj.account_collection

client_collection.find({})
client_info_list = list(client_collection.find({"group":"test_baejin"},projection={"_id":0, "client_name":1, "password":1}))

for client_info in client_info_list:
    insta_account_obj.client_name = client_info.get("client_name")
    account_info = insta_account_obj.select_cookie_user_many_v1(username=None)
    how_many_account = len(account_info)
    client_info.update(n_account=how_many_account)
print(client_info_list)
df = pd.DataFrame(client_info_list)
df.to_excel(f"test_baejin.xlsx")


# for i in range(4,11):
#     for account in range(0, 100):
#         account_info = insta_account_obj.select_cookie_user_v1(username=None)
#         account_collection.update_one({"username":account_info.get("username")}, {"$set": {"client_name": f"test_baejin_{i}"}})
#     print(f"test_baejin_{i} finish")
    # result = account_collection.update_one({"client_name": "admin_test", "status": "new"}, {"$set": {"client_name": client_name}})
    # print(result.raw_result)




