import os
from dotenv import load_dotenv
import json
load_dotenv()
DB_INFO = json.loads(os.getenv("DB_INFO"))
DB_USERNAME = DB_INFO.get("username")
DB_PASSWORD = DB_INFO.get("password")
DB_HOST = DB_INFO.get("host")
DB_PORT = DB_INFO.get("port")
DB_AUTHENTICATION_MECHANISM = DB_INFO.get("authentication_mechanism")
DB_AUTHENTICATION_SOURCE = DB_INFO.get('authentication_source')
ACCOUNT_AVAILABLE_INTERVAL_FROM_LAST_LOGIN = int(os.getenv('ACCOUNT_AVAILABLE_INTERVAL_FROM_LAST_LOGIN'))
IS_WINDOWS = bool(int(os.getenv('IS_WINDOWS')))