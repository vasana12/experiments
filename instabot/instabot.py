from contextlib import contextmanager
from datetime import datetime
from functools import wraps
from typing import Callable, List, Optional
import requests
import urllib3
from .exceptions import *
from .instabotcontext import InstabotContext, RateController
import logging
from db import m_instagram

# 로그 생성

def _requires_login(func: Callable) -> Callable:
    """Decorator to raise an exception if function is called without being logged in"""

    @wraps(func)
    def call(instaloader, *args, **kwargs):
        if not instaloader.context.is_logged_in:
            raise LoginRequiredException("--login=USERNAME required.")
        return func(instaloader, *args, **kwargs)

    return call


def _retry_on_connection_error(func: Callable) -> Callable:
    """Decorator to retry the function max_connection_attemps number of times.."""

    @wraps(func)
    def call(instaloader, *args, **kwargs):
        try:
            return func(instaloader, *args, **kwargs)
        except (urllib3.exceptions.HTTPError, requests.exceptions.RequestException, ConnectionException) as err:
            error_string = "{}({}): {}".format(func.__name__, ', '.join([repr(arg) for arg in args]), err)
            if (kwargs.get('_attempt') or 1) == instaloader.context.max_connection_attempts:
                raise ConnectionException(error_string) from None
            instaloader.context.error(error_string + " [retrying; skip with ^C]", repeat_at_end=False)
            try:
                if kwargs.get('_attempt'):
                    kwargs['_attempt'] += 1
                else:
                    kwargs['_attempt'] = 2
                instaloader.context.do_sleep()
                return call(instaloader, *args, **kwargs)
            except KeyboardInterrupt:
                instaloader.context.error("[skipped by user]", repeat_at_end=False)
                raise ConnectionException(error_string) from None

    return call


class Instabot:
    """Instaloader Class.
       The associated :class:`InstaloaderContext` with low-level communication functions and logging.
    """

    def __init__(self,
                 sleep: bool = True,
                 quiet: bool = False,
                 user_agent: Optional[str] = None,
                 save_metadata: bool = True,
                 compress_json: bool = True,
                 post_metadata_txt_pattern: str = None,
                 max_connection_attempts: int = 3,
                 request_timeout: float = 300.0,
                 rate_controller: Optional[Callable[[InstabotContext], RateController]] = None,
                 resume_prefix: Optional[str] = "iterator",
                 check_resume_bbd: bool = True,
                 slide: Optional[str] = None,
                 fatal_status_codes: Optional[List[int]] = None,
                 iphone_support: bool = True):
        # 로그 생성
        self.context = InstabotContext(sleep, quiet, user_agent, max_connection_attempts,
                                       request_timeout, rate_controller, fatal_status_codes,
                                       iphone_support)
        # configuration parameters

        self.save_metadata = save_metadata
        self.compress_json = compress_json
        self.post_metadata_txt_pattern = '{caption}' if post_metadata_txt_pattern is None \
            else post_metadata_txt_pattern
        self.resume_prefix = resume_prefix
        self.check_resume_bbd = check_resume_bbd

        self.slide = slide or ""
        self.slide_start = 0
        self.slide_end = -1
        if self.slide != "":
            splitted = self.slide.split('-')
            if len(splitted) == 1:
                if splitted[0] == 'last':
                    # download only last image of a sidecar
                    self.slide_start = -1
                else:
                    if int(splitted[0]) > 0:
                        self.slide_start = self.slide_end = int(splitted[0]) - 1
                    else:
                        raise InvalidArgumentException("--slide parameter must be greater than 0.")
            elif len(splitted) == 2:
                if splitted[1] == 'last':
                    self.slide_start = int(splitted[0]) - 1
                elif 0 < int(splitted[0]) < int(splitted[1]):
                    self.slide_start = int(splitted[0]) - 1
                    self.slide_end = int(splitted[1]) - 1
                else:
                    raise InvalidArgumentException("Invalid data for --slide parameter.")
            else:
                raise InvalidArgumentException("Invalid data for --slide parameter.")

    @contextmanager
    def anonymous_copy(self):
        """Yield an anonymous, otherwise equally-configured copy of an Instaloader instance; Then copy its error log."""
        new_loader = Instabot(
            sleep=self.context.sleep,
            quiet=self.context.quiet,
            user_agent=self.context.user_agent,
            save_metadata=self.save_metadata,
            compress_json=self.compress_json,
            post_metadata_txt_pattern=self.post_metadata_txt_pattern,
            max_connection_attempts=self.context.max_connection_attempts,
            request_timeout=self.context.request_timeout,
            resume_prefix=self.resume_prefix,
            check_resume_bbd=self.check_resume_bbd,
            slide=self.slide,
            fatal_status_codes=self.context.fatal_status_codes,
            iphone_support=self.context.iphone_support)
        yield new_loader
        self.context.error_log.extend(new_loader.context.error_log)
        new_loader.context.error_log = []  # avoid double-printing of errors
        new_loader.close()

    def close(self):
        """Close associated session objects and repeat error log."""
        self.context.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def test_login(self) -> Optional[str]:
        """Returns the Instagram username to which given :class:`requests.Session` object belongs, or None."""
        return self.context.test_login()

    def login(self, user: str, session_info: Optional[dict] = None):
        account_collection = m_instagram.InstaDB(db_name="account").db["account"]
        user_doc: dict = account_collection.find_one({"username": user}) or {}
        session_keys = ["csrftoken", "ds_user_id", "sessionid"]
        """if user is already registered in database"""
        if not (user_doc and "session" in user_doc.keys()):
            return False

        fields_not_entered = list(filter(lambda x: x not in user_doc["session"].keys(), session_keys))
        """if user and session info is already registered and session info is entirely updated, login using session info that already exists"""
        if len(fields_not_entered) > 0:
            return False

        session_info = user_doc["session"]
        self.context.logger.info(f"login using session info that already exists")
        self.context.login(user, session_info=session_info)
        return session_info

        # """1. if user is not registered"""
        # """2. if user is already registered in database but session info is not updated"""
        # """3. if user and session info is already registered in database but csrftoken is not updated"""
        # self.logger.info("login using new session")
        # session_info = None
        #
        # session_info = self.context.login(user, passwd, session_info=session_info)
        # account_collection.update_one(filter={"username": user},
        #                               update={
        #                                   "$set":
        #                                       {
        #                                           "username": user,
        #                                           "password": passwd,
        #                                           "session": session_info,
        #                                           "session_updated_datetime": datetime.now(),
        #                                       }
        #                               },
        #                               upsert=True
        #                               )
        # return session_info

    """Log in to instagram with given username and password and internally store session object.
        :raises InvalidArgumentException: If the provided username does not exist.
        :raises BadCredentialsException: If the provided password is wrong.
        :raises ConnectionException: If connection to Instagram failed"""
