from db import m_instagram
import logging
from instamanager.api.manager_exceptions import NoUserIdException
test = NoUserIdException()
if isinstance(test, NoUserIdException):
    print("sdr")