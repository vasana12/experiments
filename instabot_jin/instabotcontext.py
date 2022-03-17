import logging
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

from .exceptions import *
from db import m_instagram
logger = logging.getLogger(__name__)

# 로그의 출력 기준 설정
logger.setLevel(logging.DEBUG)

# log 출력 형식
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# log 출력
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

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
                 fatal_status_codes: Optional[List[int]] = None,
                 iphone_support: bool = True):

        self.user_agent = user_agent if user_agent is not None else default_user_agent()
        self.request_timeout = request_timeout
        self._session = requests.session()
        self.username = None
        self.sleep = sleep
        self.quiet = quiet
        self.max_connection_attempts = max_connection_attempts
        self._graphql_page_length = 50
        self._root_rhx_gis = None
        self.two_factor_auth_pending = None
        self.iphone_support = iphone_support

        # error log, filled with error() and printed at the end of Instaloader.main()
        self.error_log = []                      # type: List[str]


        # Can be set to True for testing, disables supression of InstaloaderContext._error_catcher
        self.raise_all_errors = False

        # HTTP status codes that should cause an AbortDownloadException
        self.fatal_status_codes = fatal_status_codes or []

        # Cache profile from id (mapping from id to Profile)
        self.profile_id_cache = dict()           # type: Dict[int, Any]
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


    @property
    def is_logged_in(self) -> bool:
        """True, if this Instaloader instance is logged in."""
        return bool(self.username)

    def log(self, *msg, sep='', end='\n', flush=False):
        """Log a message to stdout that can be suppressed with --quiet."""
        if not self.quiet:
            print(*msg, sep=sep, end=end, flush=flush)

    def error(self, msg, repeat_at_end=True):
        print(msg, file=sys.stderr)
        if repeat_at_end:
            self.error_log.append(msg)

    def close(self):
        """Print error log and close session"""
        if self.error_log and not self.quiet:
            print("\nErrors or warnings occurred:", file=sys.stderr)
            for err in self.error_log:
                print(err, file=sys.stderr)
        self._session.close()

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

    def _custom_http_header(self, LoginCSRFtoken):
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.120 Safari/537.36",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": "https://www.instagram.com/accounts/login/",
            "x-csrftoken": LoginCSRFtoken
        }

    def test_login(self) -> Optional[str]:
        data = self.graphql_query("d6f4427fbe92d846298cf93df0b937d3", {})
        return data["data"]["user"]["username"] if data["data"]["user"] is not None else None
    
    def login(self, user, passwd):
        """Not meant to be used directly, use :meth:`Instaloader.load_session_from_file`."""
        account_collection = m_instagram.InstaDB(db_name="account").db["account"]
        user_doc = account_collection.find_one({"username": user})
        logger.info(f"user_doc:{user_doc}")

        logger.info("load from db session")
        logger.fatal(f"user_doc:{user_doc}")
        session = requests.Session()
        link = "https://www.instagram.com/accounts/login/"
        # getCSRF = session.get(link)
        # cookieString = str(getCSRF.cookies)
        # LoginCSRFtoken = cookieString[37:69]
        logger.fatal(f"session.cookies:{session.cookies.get_dict()}")
        session.cookies.update({'sessionid': '', 'mid': '', 'ig_pr': '1',
                                'ig_vw': '1920', 'ig_cb': '1', 'csrftoken': '',
                                's_network': '', 'ds_user_id': ''})
        # Override default timeout behavior.
        # Need to silence mypy bug for this. See: https://github.com/python/mypy/issues/2427
        session.request = partial(session.request, timeout=self.request_timeout)  # type: ignore
        logger.fatal(f"load_from_session_cookie_jar:{session.cookies.get_dict()}")

        login_csrf_token = user_doc["session"]["csrftoken"]
        login_user_id = user_doc["session"]["ds_user_id"]
        login_session_id = user_doc["session"]["sessionid"]

        self.api_headers["x-csrftoken"] = self.api_headers["x-csrftoken"].format(**locals())
        self.api_headers["cookie"] = self.api_headers["cookie"].format(**locals())

        self._session = session
        self._session.headers = self.api_headers
        self.username = user

    def do_sleep(self):
        if self.sleep:
            time.sleep(min(random.expovariate(0.6), 15.0))

    def get_json(self, path: str, params: Dict[str, Any], host: str = 'www.instagram.com',
                 session: Optional[requests.Session] = None, _attempt=1) -> Dict[str, Any]:
        """JSON request to Instagram.
        """
        is_graphql_query = 'query_hash' in params and 'graphql/query' in path
        sess = session if session else self._session
        try:

            is_post = "post" in params

            if is_post:
                data = params["data"]
                name = params["name"]
                search_type = params["search_type"]
                type_url_mapping = {"hashtag":"tags","location":"locations"}
                url_type = type_url_mapping[search_type]
                logger.debug("is post")
                logger.debug(f'https://i.instagram.com/api/v1/{url_type}/{name}/sections/')
                resp = sess.post(f'https://i.instagram.com/api/v1/{url_type}/{name}/sections/',headers=self.api_headers, data=data, allow_redirects=False)
                logger.debug(resp.status_code)
            else:
                resp = sess.get('https://{0}/{1}'.format(host, path), params=params, allow_redirects=False)


            while resp.is_redirect:
                redirect_url = resp.headers['location']
                self.log('\nHTTP redirect from https://{0}/{1} to {2}'.format(host, path, redirect_url))
                if redirect_url.startswith('https://www.instagram.com/accounts/login'):
                    if not self.is_logged_in:
                        raise LoginRequiredException("Redirected to login page. Use --login.")
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
            return resp_json if not is_post else {"data":resp_json}
        except (ConnectionException, json.decoder.JSONDecodeError, requests.exceptions.RequestException) as err:
            error_string = "JSON Query to {}: {}".format(path, err)
            if _attempt == self.max_connection_attempts:
                if isinstance(err, QueryReturnedNotFoundException):
                    raise QueryReturnedNotFoundException(error_string) from err
                else:
                    raise ConnectionException(error_string) from err
            self.error(error_string + " [retrying; skip with ^C]", repeat_at_end=False)
            raise err

    def graphql_query(self, query_hash: str, variables: Dict[str, Any],
                      referer: Optional[str] = None, rhx_gis: Optional[str] = None) -> Dict[str, Any]:
        """
        Do a GraphQL Query.
        """
        with copy_session(self._session, self.request_timeout) as tmpsession:
            tmpsession.headers.update(self._default_http_header(empty_session_only=True))
            del tmpsession.headers['Connection']
            del tmpsession.headers['Content-Length']
            tmpsession.headers['authority'] = 'www.instagram.com'
            tmpsession.headers['scheme'] = 'https'
            tmpsession.headers['accept'] = '*/*'
            if referer is not None:
                tmpsession.headers['referer'] = urllib.parse.quote(referer)

            variables_json = json.dumps(variables, separators=(',', ':'))

            if rhx_gis:
                #self.log("rhx_gis {} query_hash {}".format(rhx_gis, query_hash))
                values = "{}:{}".format(rhx_gis, variables_json)
                x_instagram_gis = hashlib.md5(values.encode()).hexdigest()
                tmpsession.headers['x-instagram-gis'] = x_instagram_gis

            resp_json = self.get_json('graphql/query',
                                      params={'query_hash': query_hash,
                                              'variables': variables_json},
                                      session=tmpsession)
        if 'status' not in resp_json:
            self.error("GraphQL response did not contain a \"status\" field.")
        return resp_json

    def graphql_node_list(self, query_hash: str, query_variables: Dict[str, Any],
                          query_referer: Optional[str],
                          edge_extractor: Callable[[Dict[str, Any]], Dict[str, Any]],
                          rhx_gis: Optional[str] = None,
                          first_data: Optional[Dict[str, Any]] = None) -> Iterator[Dict[str, Any]]:
        """
        Retrieve a list of GraphQL nodes.
        """

        def _query():
            query_variables['first'] = self._graphql_page_length
            try:
                return edge_extractor(self.graphql_query(query_hash, query_variables, query_referer, rhx_gis))
            except QueryReturnedBadRequestException:
                new_page_length = int(self._graphql_page_length / 2)
                if new_page_length >= 12:
                    self._graphql_page_length = new_page_length
                    self.error("HTTP Error 400 (Bad Request) on GraphQL Query. Retrying with shorter page length.",
                               repeat_at_end=False)
                    return _query()
                else:
                    raise

        if first_data:
            data = first_data
        else:
            data = _query()
        yield from (edge['node'] for edge in data['edges'])
        while data['page_info']['has_next_page']:
            query_variables['after'] = data['page_info']['end_cursor']
            data = _query()
            yield from (edge['node'] for edge in data['edges'])

    def get_iphone_json(self, path: str, params: Dict[str, Any]) -> Dict[str, Any]:
        with copy_session(self._session, self.request_timeout) as tempsession:
            tempsession.headers['User-Agent'] = 'Instagram 146.0.0.27.125 (iPhone12,1; iOS 13_3; en_US; en-US; ' \
                                                'scale=2.00; 1656x3584; 190542906)'
            for header in ['Host', 'Origin', 'X-Instagram-AJAX', 'X-Requested-With']:
                tempsession.headers.pop(header, None)
            return self.get_json(path, params, 'i.instagram.com', tempsession)

    def write_raw(self, resp: Union[bytes, requests.Response], filename: str) -> None:

        self.log(filename, end=' ', flush=True)
        with open(filename + '.temp', 'wb') as file:
            if isinstance(resp, requests.Response):
                shutil.copyfileobj(resp.raw, file)
            else:
                file.write(resp)
        os.replace(filename + '.temp', filename)
