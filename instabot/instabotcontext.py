import hashlib
import json
import os
import pickle
import random
import re
import shutil
import sys
import textwrap
import time
import urllib.parse
from contextlib import contextmanager
from datetime import datetime, timedelta
from functools import partial
from typing import Any, Callable, Dict, Iterator, List, Optional, Union

import requests
import requests.utils
from . import config, devices
from .exceptions import *
import logging



REQUEST_HEADERS = {
    "X-IG-App-Locale": "en_US",
    "X-IG-Device-Locale": "en_US",
    "X-Pigeon-Session-Id": "21aa671b-a5f3-4093-8ec2-0c98420675e1",
    "X-Pigeon-Rawclienttime": str(round(time.time() * 1000)),
    "X-IG-Connection-Speed": "-1kbps",
    "X-IG-Bandwidth-Speed-KBPS": str(random.randint(7000, 10000)),
    "X-IG-Bandwidth-TotalBytes-B": str(random.randint(500000, 900000)),
    "X-IG-Bandwidth-TotalTime-MS": str(random.randint(50, 150)),
    "X-IG-Prefetch-Request": "foreground",
    "X-Bloks-Version-Id": "0a3ae4c88248863609c67e278f34af44673cff300bc76add965a9fb036bd3ca3",
    "X-IG-WWW-Claim": "0",
    "X-MID": "XkAyKQABAAHizpYQvHzNeBo4E9nm",
    "X-Bloks-Is-Layout-RTL": "false",
    "X-Bloks-Enable-RenderCore": "false",
    # TODO get the uuid from api_login here
    # "X-IG-Device-ID": "{uuid}",
    # TODO get the device_id from api_login here
    # "X-IG-Android-ID": "{device_id}",
    "X-IG-Connection-Type": "WIFI",
    "X-IG-Capabilities": "3brTvwE=",
    "X-IG-App-ID": "567067343352427",
    "X-IG-App-Startup-Country": "US",
    "Accept-Language": "en-US",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Accept-Encoding": "gzip, deflate",
    "Host": "i.instagram.com",
    "X-FB-HTTP-Engine": "Liger",
    "Connection": "close",
}


def copy_session(session: requests.Session, request_timeout: Optional[float] = None) -> requests.Session:
    """Duplicates a requests.Session."""
    new = requests.Session()
    new.cookies = requests.utils.cookiejar_from_dict(requests.utils.dict_from_cookiejar(session.cookies))
    new.headers = session.headers.copy()
    # Override default timeout behavior.
    # Need to silence mypy bug for this. See: https://github.com/python/mypy/issues/2427
    new.request = partial(new.request, timeout=request_timeout) # type: ignore
    return new


def default_user_agent() -> str:
    return 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' \
           '(KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36'


class InstabotContext:
    def __init__(self, sleep: bool = True, quiet: bool = False, user_agent: Optional[str] = None,
                 max_connection_attempts: int = 3, request_timeout: float = 300.0,
                 rate_controller = None,
                 fatal_status_codes: Optional[List[int]] = None,
                 iphone_support: bool = True):
        self.device = devices.DEFAULT_DEVICE
        self.user_agent = user_agent if user_agent is not None else default_user_agent()
        self.request_timeout = request_timeout
        self._session = self.get_anonymous_session()
        self.username = None
        self.sleep = sleep
        self.quiet = quiet
        self.max_connection_attempts = max_connection_attempts
        self._graphql_page_length = 50
        self._root_rhx_gis = None
        self.two_factor_auth_pending = None
        self.iphone_support = iphone_support
        self.api_headers = {'authority': 'i.instagram.com', 'sec-ch-ua': '^\\^',
                            'x-ig-www-claim': 'hmac.AR1zEkyp_49MJj9gFdNddIdOHHRRXiLFKjcUAM8aCZpTodan',
                            'sec-ch-ua-mobile': '?0', 'x-instagram-ajax': '038c8e332b43',
                            'content-type': 'application/x-www-form-urlencoded', 'accept': '*/*',
                            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36',
                            'x-asbd-id': '437806', 'x-csrftoken': "{login_csrf_token}",
                            'x-ig-app-id': '936619743392459', 'origin': 'https://www.instagram.com',
                            'sec-fetch-site': 'same-site', 'sec-fetch-mode': 'cors', 'sec-fetch-dest': 'empty',
                            'referer': 'https://www.instagram.com/',
                            'accept-language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
                            'cookie': 'ig_did=0976F080-548B-4797-9541-59CD87106A52; mid=X2V5XwALAAFXnLmEccKvAiyIVpVL; ig_nrcb=1; shbid=7030; rur=FTW; shbts=1623064813.0255795; csrftoken="{login_csrf_token}"; ds_user_id="{login_user_id}"; sessionid="{login_session_id}"', }

        # 로그 생성
        FORMAT = '%(module)s.%(funcName)s - %(message)s - %(levelname)s - %(asctime)s'
        logging.basicConfig(format=FORMAT)
        logger = logging.getLogger(__name__)
        if logger.hasHandlers():
            # Logger is already configured, remove all handlers
            logger.handlers = []
        logger.setLevel(logging.INFO)
        self.logger = logger

        self._rate_controller = rate_controller(self) if rate_controller is not None else RateController(self)

        # HTTP status codes that should cause an AbortDownloadException
        self.fatal_status_codes = fatal_status_codes or []

    @contextmanager
    def anonymous_copy(self):
        session = self._session
        username = self.username
        self._session = self.get_anonymous_session()
        self.username = None
        try:
            yield self
        finally:
            self._session.close()
            self.username = username
            self._session = session

    @property
    def is_logged_in(self) -> bool:
        """True, if this Instaloader instance is logged in."""
        return bool(self.username)

    @property
    def cookie_dict(self):
        return self._session.cookies.get_dict()

    @property
    def token(self):
        return self.cookie_dict["csrftoken"]

    @property
    def user_id(self):
        return self.cookie_dict["ds_user_id"]

    def set_device(self):
        self.device_settings = devices.DEVICES[self.device]
        self.user_agent = config.USER_AGENT_BASE.format(**self.device_settings)


    def _default_http_header(self, empty_session_only: bool = False) -> Dict[str, str]:
        """Returns default HTTP header we use for requests."""
        header = {'Accept-Encoding': 'gzip, deflate',
                  'Accept-Language': 'en-US,en;q=0.8',
                  'Connection': 'keep-alive',
                  'Content-Length': '0',
                  'Host': 'www.instagram.com',
                  'Origin': 'https://www.instagram.com',
                  'Referer': 'https://www.instagram.com/',
                  'User-Agent': self.user_agent,
                  'X-Instagram-AJAX': '1',
                  'X-Requested-With': 'XMLHttpRequest'}
        if empty_session_only:
            del header['Host']
            del header['Origin']
            del header['X-Instagram-AJAX']
            del header['X-Requested-With']
        return header

    def get_anonymous_session(self) -> requests.Session:
        """Returns our default anonymous requests.Session object."""
        session = requests.Session()
        session.cookies.update({'sessionid': '', 'mid': '', 'ig_pr': '1',
                                'ig_vw': '1920', 'csrftoken': '',
                                's_network': '', 'ds_user_id': ''})
        session.headers.update(self._default_http_header(empty_session_only=True))
        session.request = partial(session.request, timeout=self.request_timeout)
        return session

    # def get_session_info(self,session_info):
    #     if session_info
    #     return self._session.cookies.get_dict()

    def load_session_from_file(self, username, sessionfile):
        session = requests.Session()
        session.cookies = requests.utils.cookiejar_from_dict(pickle.load(sessionfile))
        session.headers.update(self._default_http_header())
        session.headers.update({'X-CSRFToken': session.cookies.get_dict()['csrftoken']})
        session.request = partial(session.request, timeout=self.request_timeout)
        self._session = session
        self.username = username


    def load_session_from_db(self, username, session_info):
        session = requests.Session()
        # username, password = 'sp22064497', 'amdc2580!'
        # proxy = f"http://user-{username}-sessionduration-1:{password}@us.smartproxy.com:10000"
        # parsed = urllib.parse.urlparse(proxy)
        # scheme = "http://" if not parsed.scheme else ""
        # session.proxies["http"] = scheme + proxy
        # session.proxies["https"] = scheme + proxy

        session.cookies = requests.utils.cookiejar_from_dict(session_info)
        session.headers.update(self._default_http_header())
        session.headers.update({'X-CSRFToken': session.cookies.get_dict()['csrftoken']})
        session.request = partial(session.request, timeout=self.request_timeout)
        login_csrf_token = session_info["csrftoken"]
        login_user_id = session_info["ds_user_id"]
        login_session_id = session_info["sessionid"]

        self.api_headers["user-agent"] = "Instagram 117.0.0.28.123 Android (28/9.0; 420dpi; 1080x1920; OnePlus; ONEPLUS A3003; OnePlus3; qcom; en_US; 180322800)"
        self.api_headers["x-csrftoken"] = self.api_headers["x-csrftoken"].format(**locals())
        self.api_headers["cookie"] = self.api_headers["cookie"].format(**locals())
        self.logger.info(self.api_headers["cookie"])
        self._session = session
        self._session.headers = self.api_headers
        self.username = username

    def test_login(self) -> Optional[str]:
        """Not meant to be used directly, use :meth:`Instaloader.test_login`."""
        data = self.graphql_query("d6f4427fbe92d846298cf93df0b937d3", {})
        return data["data"]["user"]["username"] if data["data"]["user"] is not None else None

    def login(self, user, session_info:Optional[dict]=None):
        if session_info:
            self.load_session_from_db(username=user,session_info=session_info)
            return True
        else:
            return False


    def do_sleep(self):
        """Sleep a short time if self.sleep is set. Called before each request to instagram.com."""
        if self.sleep:
            time.sleep(min(random.expovariate(0.6), 15.0))

    def get_json_v_api(self, path: str, params: Dict[str, Any], host: str = 'www.instagram.com',
                 session: Optional[requests.Session] = None, _attempt=1) -> Dict[str, Any]:
        """JSON request to Instagram.

        :param path: URL, relative to the given domain which defaults to www.instagram.com/
        :param params: GET parameters
        :param host: Domain part of the URL from where to download the requested JSON; defaults to www.instagram.com
        :param session: Session to use, or None to use self.session
        :return: Decoded response dictionary
        :raises QueryReturnedBadRequestException: When the server responds with a 400.
        :raises QueryReturnedNotFoundException: When the server responds with a 404.
        :raises ConnectionException: When query repeatedly failed.
        """
        is_graphql_query = 'query_hash' in params and 'graphql/query' in path
        is_iphone_query = host == 'i.instagram.com'
        is_other_query = not is_graphql_query and host == "www.instagram.com"
        sess = session if session else self._session
        try:
            self.do_sleep()
            if is_graphql_query:
                self._rate_controller.wait_before_query(params['query_hash'])
            if is_iphone_query:
                self._rate_controller.wait_before_query('iphone')
            if is_other_query:
                self._rate_controller.wait_before_query('other')

            is_post = "post" in params

            if is_post:
                data = params["data"]
                name = params["name"]
                search_type = params["search_type"]
                type_url_mapping = {"hashtag": "tags", "location": "locations"}
                url_type = type_url_mapping[search_type]
                self.logger.info("is post")
                self.logger.info(f'POST to endpoint - https://i.instagram.com/api/v1/{url_type}/{name}/sections/')
                resp = sess.post(f'https://i.instagram.com/api/v1/{url_type}/{name}/sections/',headers=self.api_headers, data=data, allow_redirects=False)

            else:
                resp = sess.get('https://{0}/{1}'.format(host, path), params=params, allow_redirects=False)
            if resp.status_code in self.fatal_status_codes:
                redirect = " redirect to {}".format(resp.headers['location']) if 'location' in resp.headers else ""
                raise AbortDownloadException("Query to https://{}/{} responded with \"{} {}\"{}".format(
                    host, path, resp.status_code, resp.reason, redirect
                ))
            while resp.is_redirect:
                redirect_url = resp.headers['location']

                self.logger.info('\nHTTP redirect from https://{0}/{1} to {2}'.format(host, path, redirect_url))
                if redirect_url.startswith('https://www.instagram.com/accounts/login'):
                    if not self.is_logged_in:
                        raise LoginRequiredException("Redirected to login page. Use --login.")
                    # alternate rate limit exceeded behavior
                    raise TooManyRequestsException("Redirected to login")
                if redirect_url.startswith('https://{}/'.format(host)):
                    resp = sess.get(redirect_url if redirect_url.endswith('/') else redirect_url + '/',
                                    params=params, allow_redirects=False)
                else:
                    break

            ###다른 아이디로 로그인 해야함
            if resp.status_code == 400:
                raise QueryReturnedBadRequestException("400 Bad Request")
            if resp.status_code == 404:
                raise QueryReturnedNotFoundException("404 Not Found")
            if resp.status_code == 429:
                raise TooManyRequestsException("429 Too Many Requests")
            if resp.status_code != 200:
                raise ConnectionException("HTTP error code {}.".format(resp.status_code))

            is_html_query = not is_graphql_query and not "__a" in params and host == "www.instagram.com" and not is_post
            if is_html_query:
                match = re.search(r'window\._sharedData = (.*);</script>', resp.text)
                if match is None:
                    raise QueryReturnedNotFoundException("Could not find \"window._sharedData\" in html response.")
                resp_json = json.loads(match.group(1))
                entry_data = resp_json.get('entry_data')

                post_or_profile_page = list(entry_data.values())[0] if entry_data is not None else None
                if post_or_profile_page is None:
                    raise ConnectionException("\"window._sharedData\" does not contain required keys.")
                # If GraphQL data is missing in `window._sharedData`, search for it in `__additionalDataLoaded`.
                if 'graphql' not in post_or_profile_page[0]:
                    match = re.search(r'window\.__additionalDataLoaded\(.*?({.*"graphql":.*})\);</script>',
                                      resp.text)
                    if match is not None:
                        post_or_profile_page[0]['graphql'] = json.loads(match.group(1))['graphql']
                return resp_json
            else:
                resp_json = resp.json()
            if 'status' in resp_json and resp_json['status'] != "ok":
                if 'message' in resp_json:
                    raise ConnectionException("Returned \"{}\" status, message \"{}\".".format(resp_json['status'],
                                                                                               resp_json['message']))
                else:
                    raise ConnectionException("Returned \"{}\" status.".format(resp_json['status']))
            return resp_json if not is_post else {"data": resp_json}
        except (ConnectionException, json.decoder.JSONDecodeError, requests.exceptions.RequestException) as err:
            error_string = "JSON Query to {}: {}".format(path, err)
            if _attempt == self.max_connection_attempts:
                if isinstance(err, QueryReturnedNotFoundException):
                    raise QueryReturnedNotFoundException(error_string) from err
                else:
                    raise ConnectionException(error_string) from err
            self.logger.error(error_string + " [retrying; skip with ^C]")
            try:
                if isinstance(err, TooManyRequestsException):
                    if is_graphql_query:
                        self._rate_controller.handle_429(params['query_hash'])
                    if is_iphone_query:
                        self._rate_controller.handle_429('iphone')
                    if is_other_query:
                        self._rate_controller.handle_429('other')
                return self.get_json_v_api(path=path, params=params, host=host, session=sess, _attempt=_attempt + 1)
            except KeyboardInterrupt:
                self.logger.error("[skipped by user]")
                raise ConnectionException(error_string) from err

    def get_json(self, path: str, params: Dict[str, Any], host: str = 'www.instagram.com',
                 session: Optional[requests.Session] = None, _attempt=1, data=None) -> Dict[str, Any]:
        """JSON request to Instagram.

        :param path: URL, relative to the given domain which defaults to www.instagram.com/
        :param params: GET parameters
        :param host: Domain part of the URL from where to download the requested JSON; defaults to www.instagram.com
        :param session: Session to use, or None to use self.session
        :return: Decoded response dictionary
        :raises QueryReturnedBadRequestException: When the server responds with a 400.
        :raises QueryReturnedNotFoundException: When the server responds with a 404.
        :raises ConnectionException: When query repeatedly failed.
        """
        is_graphql_query = 'query_hash' in params and 'graphql/query' in path
        is_iphone_query = host == 'i.instagram.com'
        is_other_query = not is_graphql_query and host == "www.instagram.com"
        sess = session if session else self._session
        try:
            self.do_sleep()
            if is_graphql_query:
                self._rate_controller.wait_before_query(params['query_hash'])
            if is_iphone_query:
                self._rate_controller.wait_before_query('iphone')
            if is_other_query:
                self._rate_controller.wait_before_query('other')

            if is_graphql_query:
                url = 'https://{0}/{1}'.format(host, path)
                resp = sess.get(
                    url="https://app.scrapingbee.com/api/v1/",
                    params={
                        "api_key": "XAZN5Y277PEU020TOQWCSZL8PXCM3AKBZPXTX67S6ZBO7Y7QXC9WTV0T7O2EK4QRWR0O2I3Z0F0EM92X",
                        "url": 'https://{0}/{1}'.format(host, path),
                        "render_js": "false",
                        "params": params,
                        "allow_redirects": False
                    },
                )
            else:
                resp = sess.get('https://{0}/{1}'.format(host, path), params=params, allow_redirects=False)
            if resp.status_code in self.fatal_status_codes:
                redirect = " redirect to {}".format(resp.headers['location']) if 'location' in resp.headers else ""
                raise AbortDownloadException("Query to https://{}/{} responded with \"{} {}\"{}".format(
                    host, path, resp.status_code, resp.reason, redirect
                ))
            while resp.is_redirect:
                redirect_url = resp.headers['location']
                self.logger.info('\nHTTP redirect from https://{0}/{1} to {2}'.format(host, path, redirect_url))
                if redirect_url.startswith('https://www.instagram.com/accounts/login'):
                    if not self.is_logged_in:
                        raise LoginRequiredException("Redirected to login page. Use --login.")
                    # alternate rate limit exceeded behavior
                    raise TooManyRequestsException("Redirected to login")
                if redirect_url.startswith('https://{}/'.format(host)):
                    resp = sess.get(redirect_url if redirect_url.endswith('/') else redirect_url + '/',
                                    params=params, allow_redirects=False)
                else:
                    break

            if resp.status_code == 400:
                raise QueryReturnedBadRequestException("400 Bad Request")
            if resp.status_code == 404:
                raise QueryReturnedNotFoundException("404 Not Found")
            if resp.status_code == 429:
                raise TooManyRequestsException("429 Too Many Requests")
            if resp.status_code != 200:
                raise ConnectionException("HTTP error code {}.".format(resp.status_code))
            is_html_query = not is_graphql_query and not "__a" in params and host == "www.instagram.com"
            if is_html_query:
                match = re.search(r'window\._sharedData = (.*);</script>', resp.text)
                if match is None:
                    raise QueryReturnedNotFoundException("Could not find \"window._sharedData\" in html response.")
                resp_json = json.loads(match.group(1))
                entry_data = resp_json.get('entry_data')
                post_or_profile_page = list(entry_data.values())[0] if entry_data is not None else None
                if post_or_profile_page is None:
                    raise ConnectionException("\"window._sharedData\" does not contain required keys.")
                # If GraphQL data is missing in `window._sharedData`, search for it in `__additionalDataLoaded`.
                if 'graphql' not in post_or_profile_page[0]:
                    match = re.search(r'window\.__additionalDataLoaded\(.*?({.*"graphql":.*})\);</script>',
                                      resp.text)
                    if match is not None:
                        post_or_profile_page[0]['graphql'] = json.loads(match.group(1))['graphql']
                return resp_json
            else:
                resp_json = resp.json()
            if 'status' in resp_json and resp_json['status'] != "ok":
                if 'message' in resp_json:
                    raise ConnectionException("Returned \"{}\" status, message \"{}\".".format(resp_json['status'],
                                                                                               resp_json['message']))
                else:
                    raise ConnectionException("Returned \"{}\" status.".format(resp_json['status']))
            return resp_json
        except (ConnectionException, json.decoder.JSONDecodeError, requests.exceptions.RequestException) as err:
            error_string = "JSON Query to {}: {}".format(path, err)
            if _attempt == self.max_connection_attempts:
                if isinstance(err, QueryReturnedNotFoundException):
                    raise QueryReturnedNotFoundException(error_string) from err
                else:
                    raise ConnectionException(error_string) from err
            self.logger.error(error_string + " [retrying; skip with ^C]")
            try:
                if isinstance(err, TooManyRequestsException):
                    if is_graphql_query:
                        self._rate_controller.handle_429(params['query_hash'])
                    if is_iphone_query:
                        self._rate_controller.handle_429('iphone')
                    if is_other_query:
                        self._rate_controller.handle_429('other')
                return self.get_json(path=path, params=params, host=host, session=sess, _attempt=_attempt + 1)
            except KeyboardInterrupt:
                self.logger.error("[skipped by user]")
                raise ConnectionException(error_string) from err

    def graphql_query(self, query_hash: str, variables: Dict[str, Any],
                      referer: Optional[str] = None, rhx_gis: Optional[str] = None) -> Dict[str, Any]:


        variables_json = json.dumps(variables, separators=(',', ':'))

        if rhx_gis:
            #self.log("rhx_gis {} query_hash {}".format(rhx_gis, query_hash))
            values = "{}:{}".format(rhx_gis, variables_json)
            x_instagram_gis = hashlib.md5(values.encode()).hexdigest()
            self._session.headers['x-instagram-gis'] = x_instagram_gis

        resp_json = self.get_json_v_api('graphql/query',
                                  params={'query_hash': query_hash,
                                          'variables': variables_json})
        if 'status' not in resp_json:
            self.logger.error("GraphQL response did not contain a \"status\" field.")
        return resp_json

    def get_iphone_json(self, path: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """JSON request to ``i.instagram.com``.

        :param path: URL, relative to ``i.instagram.com/``
        :param params: GET parameters
        :return: Decoded response dictionary
        :raises QueryReturnedBadRequestException: When the server responds with a 400.
        :raises QueryReturnedNotFoundException: When the server responds with a 404.
        :raises ConnectionException: When query repeatedly failed"""

        with copy_session(self._session, self.request_timeout) as tempsession:
            tempsession.headers['User-Agent'] = 'Instagram 146.0.0.27.125 (iPhone12,1; iOS 13_3; en_US; en-US; ' \
                                                'scale=2.00; 1656x3584; 190542906)'
            for header in ['Host', 'Origin', 'X-Instagram-AJAX', 'X-Requested-With']:
                tempsession.headers.pop(header, None)
            return self.get_json(path, params, 'i.instagram.com', tempsession)



    def head(self, url: str, allow_redirects: bool = False) -> requests.Response:
        """HEAD a URL anonymously.
        :raises QueryReturnedNotFoundException: When the server responds with a 404.
        :raises QueryReturnedForbiddenException: When the server responds with a 403.
        :raises ConnectionException: When request failed.
        """
        with self.get_anonymous_session() as anonymous_session:
            resp = anonymous_session.head(url, allow_redirects=allow_redirects)
        if resp.status_code == 200:
            return resp
        else:
            if resp.status_code == 403:
                # suspected invalid URL signature
                raise QueryReturnedForbiddenException("403 when accessing {}.".format(url))
            if resp.status_code == 404:
                # 404 not worth retrying.
                raise QueryReturnedNotFoundException("404 when accessing {}.".format(url))
            raise ConnectionException("HTTP error code {}.".format(resp.status_code))

    @property
    def root_rhx_gis(self) -> Optional[str]:
        """rhx_gis string returned in the / query."""
        if self.is_logged_in:
            # At the moment, rhx_gis seems to be required for anonymous requests only. By returning None when logged
            # in, we can save the root_rhx_gis lookup query.
            return None
        if self._root_rhx_gis is None:
            self._root_rhx_gis = self.get_json('', {}).get('rhx_gis', '')
        return self._root_rhx_gis or None


class RateController:
    """
    Class providing request tracking and rate controlling to stay within rate limits.
       import instabot

       class MyRateController(instabot.RateController):
           def sleep(self, secs):
               raise MyCustomException()

       L = instabot(rate_controller=lambda x: MyRateController(x))
    """

    def __init__(self, context: InstabotContext):
        self._context = context
        self._query_timestamps = dict()  # type: Dict[str, List[float]]
        self._earliest_next_request_time = 0.0
        self._iphone_earliest_next_request_time = 0.0
        self.logger = context.logger
    def sleep(self, secs: float):
        """Wait given number of seconds."""
        # Not static, to allow for the behavior of this method to depend on context-inherent properties, such as
        # whether we are logged in.
        # pylint:disable=no-self-use
        time.sleep(secs)

    def _dump_query_timestamps(self, current_time: float, failed_query_type: str):
        windows = [10, 11, 20, 22, 30, 60]
        self.logger.error(f"Number of requests within last {'/'.join(str(w) for w in windows)} minutes grouped by type:")
        for query_type, times in self._query_timestamps.items():
            reqs_in_sliding_window = [sum(t > current_time - w * 60 for t in times) for w in windows]
            self.logger.error(" {} {:>32}: {}".format("*" if query_type == failed_query_type else " ", query_type, " ".join("{:4}".format(reqs) for reqs in reqs_in_sliding_window)))

    def count_per_sliding_window(self, query_type: str) -> int:
        """Return how many requests of the given type can be done within a sliding window of 11 minutes.

        This is called by :meth:`RateController.query_waittime` and allows to simply customize wait times before queries
        at query_type granularity. Consider overriding :meth:`RateController.query_waittime` directly if you need more
        control."""
        # Not static, to allow for the count_per_sliding_window to depend on context-inherent properties, such as
        # whether we are logged in.
        # pylint:disable=no-self-use
        return 75 if query_type == 'other' else 200

    def _reqs_in_sliding_window(self, query_type: Optional[str], current_time: float, window: float) -> List[float]:
        if query_type is not None:
            # timestamps of type query_type
            relevant_timestamps = self._query_timestamps[query_type]
        else:
            # all GraphQL queries, i.e. not 'iphone' or 'other'
            graphql_query_timestamps = filter(lambda tp: tp[0] not in ['iphone', 'other'],
                                              self._query_timestamps.items())
            relevant_timestamps = [t for times in (tp[1] for tp in graphql_query_timestamps) for t in times]
        return list(filter(lambda t: t > current_time - window, relevant_timestamps))

    def query_waittime(self, query_type: str, current_time: float, untracked_queries: bool = False) -> float:
        """Calculate time needed to wait before query can be executed."""
        per_type_sliding_window = 660
        iphone_sliding_window = 1800
        if query_type not in self._query_timestamps:
            self._query_timestamps[query_type] = []
        self._query_timestamps[query_type] = list(filter(lambda t: t > current_time - 60 * 60,
                                                         self._query_timestamps[query_type]))

        def per_type_next_request_time():
            reqs_in_sliding_window = self._reqs_in_sliding_window(query_type, current_time, per_type_sliding_window)
            if len(reqs_in_sliding_window) < self.count_per_sliding_window(query_type):
                return 0.0
            else:
                return min(reqs_in_sliding_window) + per_type_sliding_window + 6

        def gql_accumulated_next_request_time():
            if query_type in ['iphone', 'other']:
                return 0.0
            gql_accumulated_sliding_window = 600
            gql_accumulated_max_count = 275
            reqs_in_sliding_window = self._reqs_in_sliding_window(None, current_time, gql_accumulated_sliding_window)
            if len(reqs_in_sliding_window) < gql_accumulated_max_count:
                return 0.0
            else:
                return min(reqs_in_sliding_window) + gql_accumulated_sliding_window

        def untracked_next_request_time():
            if untracked_queries:
                if query_type == "iphone":
                    reqs_in_sliding_window = self._reqs_in_sliding_window(query_type, current_time,
                                                                          iphone_sliding_window)
                    self._iphone_earliest_next_request_time = min(reqs_in_sliding_window) + iphone_sliding_window + 18
                else:
                    reqs_in_sliding_window = self._reqs_in_sliding_window(query_type, current_time,
                                                                          per_type_sliding_window)
                    self._earliest_next_request_time = min(reqs_in_sliding_window) + per_type_sliding_window + 6
            return max(self._iphone_earliest_next_request_time, self._earliest_next_request_time)

        def iphone_next_request():
            if query_type == "iphone":
                reqs_in_sliding_window = self._reqs_in_sliding_window(query_type, current_time, iphone_sliding_window)
                if len(reqs_in_sliding_window) >= 199:
                    return min(reqs_in_sliding_window) + iphone_sliding_window + 18
            return 0.0

        return max(0.0,
                   max(
                       per_type_next_request_time(),
                       gql_accumulated_next_request_time(),
                       untracked_next_request_time(),
                       iphone_next_request(),
                   ) - current_time)

    def wait_before_query(self, query_type: str) -> None:
        """This method is called before a query to Instagram.

        It calls :meth:`RateController.query_waittime` to determine the time needed to wait and then calls
        :meth:`RateController.sleep` to wait until the request can be made."""
        waittime = self.query_waittime(query_type, time.monotonic(), False)
        assert waittime >= 0
        if waittime > 15:
            formatted_waittime = ("{} seconds".format(round(waittime)) if waittime <= 666 else
                                  "{} minutes".format(round(waittime / 60)))
            self.logger.info("\nToo many queries in the last time. Need to wait {}, until {:%H:%M}."
                              .format(formatted_waittime, datetime.now() + timedelta(seconds=waittime)))
        if waittime > 0:
            self.sleep(waittime)
        if query_type not in self._query_timestamps:
            self._query_timestamps[query_type] = [time.monotonic()]
        else:
            self._query_timestamps[query_type].append(time.monotonic())

    def handle_429(self, query_type: str) -> None:
        """This method is called to handle a 429 Too Many Requests response.

        It calls :meth:`RateController.query_waittime` to determine the time needed to wait and then calls
        :meth:`RateController.sleep` to wait until we can repeat the same request."""
        current_time = time.monotonic()
        waittime = self.query_waittime(query_type, current_time, True)
        assert waittime >= 0,"wait time must be greater than or equal to 0"
        self._dump_query_timestamps(current_time, query_type)
        text_for_429 = "Instagram responded with HTTP error 429 - Too Many Requests."
        self.logger.error(text_for_429)

        if waittime > 1.5:
            formatted_waittime = ("{} seconds".format(round(waittime)) if waittime <= 666 else
                                  "{} minutes".format(round(waittime / 60)))
            self.logger.error("The request will be retried in {}, at {:%H:%M}."
                                .format(formatted_waittime, datetime.now() + timedelta(seconds=waittime)))
        if waittime > 0:
            self.sleep(waittime)
