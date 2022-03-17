import re
from collections import namedtuple
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Iterable
import logging
import copy
from .exceptions import *
from .instabotcontext import InstabotContext
from .nodeiterator import NodeIterator

logger = logging.getLogger(__name__)

# 로그의 출력 기준 설정
logger.setLevel(logging.WARNING)

# log 출력 형식
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# log 출력
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

PostSidecarNode = namedtuple('PostSidecarNode', ['is_video', 'display_url', 'video_url'])


PostComment = namedtuple('PostComment',['id', 'created_at_utc', 'text', 'owner', 'likes_count']) # type: ignore

PostLocation = namedtuple('PostLocation', ['id', 'name', 'slug', 'has_public_page', 'lat', 'lng'])

class Post:
    def __init__(self, context: InstabotContext, node: Dict[str, Any],
                  next_max_id:Optional = None, next_page:Optional = None, search_type = None):
        assert 'shortcode' in node or 'code' in node
        self._context = context
        self._node = node
        self._full_metadata_dict = None  # type: Optional[Dict[str, Any]]
        self._iphone_struct_ = None
        self.next_max_id = next_max_id
        self.next_page = next_page
        self.search_type = search_type
        logger.debug(f"init self._node:{self._node}")

    def get_comments(self) -> Iterable[PostComment]:
        """ Iterate all comments of the post
            field : text(string), created_at (datetime), id (int), owner (:class: 'Profile')
        """

        def _postcomment(node):
            return PostComment(id=int(node['id']),
                               created_at_utc=datetime.utcfromtimestamp(node['created_at']),
                               text=node['text'],
                               owner=Profile(self._context, node['owner']),
                               likes_count=node.get('edge_liked_by', {}).get('count', 0))

        if self.comments == 0:
            # if there are no comments return
            return []

        return NodeIterator(
            self._context,
            '97b41c52301f77ce508f55e66d17620e',
            lambda d: d['data']['shortcode_media']['edge_media_to_parent_comment'],
            _postcomment,
            {'shortcode': self.shortcode},
            'https://www.instagram.com/p/{0}/'.format(self.shortcode),
        )

    @property
    def to_dict(self) -> dict:
        d = {'shortcode': self.shortcode, 'clean_url': self.clean_url, 'mediaid': self.mediaid,
             'media_type': self.media_type, 'post_datetime': self.post_datetime, 'likes': self.likes,
             'comments': self.comments, 'title': self.title, 'preview_comments': self.preview_comments,
             'caption': self.caption, 'user': self.user, 'hashtags': self.hashtags,
             'caption_hashtags': self.caption_hashtags}
        return d

    @property
    def shortcode(self) -> str:
        return self._node['shortcode'] if 'shortcode' in self._node else self._node['code']

    @property
    def clean_url(self) -> str:
        default_url = "https://www.instagram.com/p"
        return f"{default_url}/{self.shortcode}/"

    @property
    def mediaid(self) -> str:
        return str(self._node['id'])

    @property
    def media_type(self) -> int:
        try :
            return int(self._node['media_type'])
        except :
            return None

    @property
    def post_datetime(self) -> datetime:
        try :
            return datetime.utcfromtimestamp(self._node['taken_at'])
        except :
            return None

    @property
    def likes(self) -> int:
        """Likes count"""
        if "like_count" in self._node:
            try:
                return self._node["like_count"]
            except KeyError:
                pass

    @property
    def comments(self) -> int:
        """Comment count"""
        try:
            return self._node["comment_count"]
        except KeyError:
            pass

    @property
    def title(self) -> Optional[str]:
        try:
            return self._field('title')
        except KeyError:
            return None

    def _obtain_metadata(self):
        if not self._full_metadata_dict:
            pic_json = self._context.graphql_query(
                '2b0673e0dc4580674a88d426fe00ea90',
                {'shortcode': self.shortcode}
            )
            self._full_metadata_dict = pic_json['data']['shortcode_media']
            if self._full_metadata_dict is None:
                raise BadResponseException("Fetching Post metadata failed.")
            if self.shortcode != self._full_metadata_dict['shortcode']:
                self._node.update(self._full_metadata_dict)
                raise PostChangedException
        
    @property
    def _full_metadata(self) -> Dict[str, Any]:
        self._obtain_metadata()
        assert self._full_metadata_dict is not None
        return self._full_metadata_dict



    def _field(self, *keys) -> Any:
        try:
            d = self._node
            for key in keys:
                d = d[key]
            return d
        except KeyError:
            logger.warning("keyerror")
            d = self._full_metadata
            for key in keys:
                d = d[key]
            return d

    @property
    def typename(self) -> str:
        """Type of post, GraphImage, GraphVideo or GraphSidecar"""
        return self._field('__typename')

    @property
    def image(self):
        def map_select_first_image(carousel):
            carousel["image_versions2"]["candidates"] = carousel["image_versions2"]["candidates"][0]
            carousel["image_versions2"]["candidates"]["is_video"] = False
            if "accessibility_caption" in carousel["image_versions2"]["candidates"]:
                carousel["image_versions2"]["candidates"]["accessibility_caption"] = carousel["accessibility_caption"]
            return carousel["image_versions2"]["candidates"]
        
        if self._context.is_logged_in and self.search_type !="user":
            """Image"""
            if "carousel_media" in self._node:
                try:
                    carousel_list = self._node['carousel_media']
                    return list(map(lambda x : map_select_first_image(x) ,carousel_list))
                except Exception as e:
                    logger.debug(f"carousel error :{e}")
                    logger.debug(f"carousel_media_return None:{self._node}")
                    return None

            else:
                try:
                    if "accessibility_caption" in self._node:
                        self._node["image_versions2"]["candidates"][0]["accessibility_caption"] = self._node["accessibility_caption"]
                    self._node["image_versions2"]["candidates"][0]["is_video"] = False
                    return [self._node["image_versions2"]["candidates"][0]]
                except Exception as e:
                    logger.debug(f"image_version2 error :{e}")
                    logger.debug(f"image_version2 return None:{self._node}")
                    return None
        else:
            if "edge_sidecar_to_children" in self._node:
                try:
                    image_list = []
                    for edge in self._node["edge_sidecar_to_children"]["edges"]:
                        node = edge["node"]
                        image = {}
                        image["width"] = node["dimensions"]["width"]
                        image["height"] = node["dimensions"]["height"]
                        image["url"] = node["display_url"]
                        image["is_video"] = node["is_video"]
                        if "accessibility_caption" in node:
                            image["accessibility_caption"] = node["accessibility_caption"] 
                        
                        image_list.append(image)
                    return image_list
                except Exception as e:
                    logger.debug(f"error:{e}")
                    
    @property
    def contents(self):
        def map_select_first_image(carousel):

            carousel["image_versions2"]["candidates"] = carousel["image_versions2"]["candidates"][0]
            carousel["image_versions2"]["candidates"]["is_video"] = False
            if "accessibility_caption" in carousel["image_versions2"]["candidates"]:
                carousel["image_versions2"]["candidates"]["accessibility_caption"] = carousel["accessibility_caption"]
            return carousel["image_versions2"]["candidates"]

        def video_node(node):
            content = {}
            if node["__typename"] == "GraphVideo":
                content["is_video"] = node["is_video"]
                content["url"] = node["video_url"]
                content["video_view_count"] = node["video_view_count"]
                content["video_duration"] = node["video_duration"] if "video_duration" in node else None
                content["accessibility_caption"] = node["accessibility_caption"] if "accessibility_caption" in node else None
                return content

        def image_node(node):

            content = {}
            content["is_video"] = node["is_video"]
            content["url"] = node["display_url"]
            content["width"] = node["dimensions"]["width"]
            content["height"] = node["dimensions"]["height"]
            
            if "accessibility_caption" in node:
                content["accessibility_caption"] = node["accessibility_caption"]
            return content

        if self.search_type == "user":
            
            content = {}
            content_list = []
            node = self._node.copy()
            
            if node["__typename"] == "GraphVideo":
                content_list = [video_node(node)]
            elif node["__typename"] == "GraphImage":
                content_list = [image_node(node)]

            elif node["__typename"] == "GraphSidecar":
                if "edge_sidecar_to_children" in node:
                    for edge in node["edge_sidecar_to_children"]["edges"]:
                        if edge["node"]["__typename"] == "GraphVideo":
                             content = video_node(edge["node"])
                             content_list.append(content)
                        elif edge["node"]["__typename"] == "GraphImage":
                             image_node(edge["node"])
                             content = image_node(edge["node"])
                             content_list.append(content)
            return content_list

        elif self.search_type != "user":
            node = copy.deepcopy(self._node)
            if "view_count" not in node:
                """Image"""
                if "carousel_media" in node:
                    """multiple images"""
                    try:
                        logger.debug(f"바뀌기 전  self._node:{self._node}")

                        carousel_list = node['carousel_media']
                        return_contents = list(map(lambda x : map_select_first_image(x) ,carousel_list))
                        logger.debug(f"바뀌고 난 후 : self._node:{self._node}")
                        return return_contents
                    except Exception as e:
                        logger.debug(f"error : self._node:{self._node}")
                        logger.debug(f"carousel error :{e}")

                        return None

                else:
                    """one images"""

                    try:
                        if "accessibility_caption" in node:
                            logger.debug(f"accessibility_caption ")
                            node["image_versions2"]["candidates"][0]["accessibility_caption"] = node["accessibility_caption"]
                            node["image_versions2"]["candidates"][0]["is_video"] = False

                        return [node["image_versions2"]["candidates"][0]]
                    except Exception as e:
                        logger.debug(f"image_version2 error :{e}")
                        logger.debug(f"image_version2 return None:{self._node}")
                        return None
            else:
                """Video"""
                logger.debug(f"video")
                content = {}
                content["is_video"] = True
                content["view_count"] = self._node["view_count"]
                content["video_codec"] = self._node["video_codec"]
                content["video_duration"] = self._node["video_duration"] if "video_duration" in self._node else None
                content["width"] = self._node["video_versions"][0]["width"]
                content["height"] = self._node["video_versions"][0]["height"]
                content["url"] = self._node["video_versions"][0]["url"]
                return [content]

    @property
    def preview_comments(self) -> List[str]:
        if "preview_comments" in self._node :
            try:
                preview_comments = []
                for comment_content in self._node['preview_comments']:
                    preview_comment = comment_content['text']
                    preview_comment = preview_comment.replace("\n", "")
                    preview_comment = re.sub("\s+", " ", preview_comment)
                    preview_comments.append(preview_comment)
                return preview_comments
            except Exception as ex:
                print(ex)
                return []
        else :
            return []

    @property
    def caption(self) -> Optional[str]:
        #logger.fatal(f"{self._node}")
        """Caption."""
        if self._context.is_logged_in and self.search_type != 'user':
            if "caption" in self._node and self._node["caption"] is not None:
                try:
                    caption = self._node["caption"]["text"]
                    caption = caption.replace("\n", "")
                    caption = re.sub("\s+", " ", caption)
                    return caption
                except:
                    return None
            return None
        
        else:
            if "edge_media_to_caption" in self._node and self._node["edge_media_to_caption"]["edges"]:
                try:
                    caption = self._node['edge_media_to_caption']['edges'][0]['node']['text']
                    caption = caption.replace("\n", "")
                    caption = re.sub("\s+", " ", caption)
                    return caption
                except:
                    return None
            elif "caption" in self._node:
                try:
                    caption = self._node["caption"]["text"]
                    caption = caption.replace("\n", "")
                    caption = re.sub("\s+", " ", caption)
                    return caption
                except:
                    return None
            return None

    # @property
    # def accessibility_caption(self):
    #     "accessibility_caption"
    #     if self._context.is_logged_in:
    @property
    def user(self):
        """user_info"""
        if self._context.is_logged_in:
            if "caption" in self._node and self._node["caption"] is not None:
                try:
                    return self._node["caption"]["user"]
                except:
                    logger.debug(f"user_property self._node:{self._node}")
                    return None
            elif "user" in self._node:
                try:
                    return self._node["user"]
                except:
                    logger.debug(f"user_property self._node:{self._node}")
                    return None
            return None
    @property
    def caption_hashtags(self) -> List[str]:
        if not self.caption:
            return []
        hashtag_regex = re.compile(r"(?:#)(\w(?:(?:\w|(?:\.(?!\.))){0,28}(?:\w))?)")
        return re.findall(hashtag_regex, self.caption.lower())
    @property
    def hashtags(self) -> List[str]:
        if not self.caption and not self.preview_comments:
            return []
        hashtag_regex = re.compile(r"(?:#)(\w(?:(?:\w|(?:\.(?!\.))){0,28}(?:\w))?)")
        contents = ([self.caption] if self.caption else []) + (self.preview_comments if self.preview_comments else [])
        hashtags = [hashtag for text in contents for hashtag in re.findall(hashtag_regex, text.lower())]
        return hashtags

class PostUserNotLogin(Post):
    @property
    def post_datetime(self):
        try:
            return datetime.utcfromtimestamp(self._node['taken_at_timestamp'])
        except:
            return None

    @property
    def likes(self):
        try:
            return self._node['edge_liked_by']['count']
        except:
            return None

    @property
    def comments(self):
        try:
            return self._node['edge_media_to_comment']['count']
        except:
            return None

    @property
    def user(self):
        try:
            return self._node['owner']['username']
        except:
            return None


class Hashtag:

    def __init__(self, context: InstabotContext, node: Dict[str, Any]):
        assert "name" in node
        self._context = context
        self._node = node
        self._has_full_metadata = False
        self.next_max_id = None
        self.next_page = None

    @classmethod
    def from_name(cls, context: InstabotContext, name: str):
        # try:
        logger.debug("from_name method")
        hashtag = cls(context, {'name': name.lower()})
        hashtag._obtain_metadata()
        logger.debug(f"hashtag._obtain_metadata():{hashtag}")
        return hashtag
        # except Exception as e:
        #     return e

    @property
    def name(self):
        """Hashtag name lowercased, without preceeding '#'"""
        return self._node["name"].lower()

    def _query(self, params):

        if not self._context.is_logged_in:
            print(self._context.get_json("explore/tags/{0}/".format(self.name),
                                         params)["graphql"]["hashtag"])
            return self._context.get_json("explore/tags/{0}/".format(self.name),
                                          params)["graphql"]["hashtag"]
        else:

            return self._context.get_json("explore/tags/{0}/".format(self.name), params)["data"]

    def _obtain_metadata(self):
        logger.info("_obtain_metadata 에 들어왔습니다.")
        if not self._has_full_metadata:
            self._node = self._query({"__a": 1})

            self._has_full_metadata = True
        # logger.info(f"_obtain_metadata 에 들어왔습니다.node:{self._node}")


    def _metadata(self, *keys) -> Any:
        logger.debug(f"metadata에 들어왔습니다.{(keys)}")
        try:
            d = self._node
            for key in keys:
                try:
                    d = d[key]
                except:
                    return
            return d
        except KeyError:
            logger.debug(f"metadata에 들어왔습니다.{(keys)}, key_error")
            self._obtain_metadata()
            d = self._node
            for key in keys:
                d = d[key]
            return d

    @property
    def hashtagid(self) -> int:
        return int(self._metadata("id"))

    @property
    def profile_pic_url(self) -> str:
        return self._metadata("profile_pic_url")

    @property
    def description(self) -> str:
        return self._metadata("description")

    @property
    def allow_following(self) -> bool:
        return self._metadata("allow_following")

    @property
    def is_following(self) -> bool:
        return self._metadata("is_following")

    @property
    def is_top_media_only(self) -> bool:
        return self._metadata("is_top_media_only")

    def get_related_tags(self) -> Iterator["Hashtag"]:
        """Yields similar hashtags."""
        yield from (Hashtag(self._context, edge["node"])
                    for edge in self._metadata("edge_hashtag_to_related_tags", "edges"))

    def get_top_posts(self, next_max_id=None, next_page=None) -> Iterator[Post]:
        if not self._context.is_logged_in:
            """Yields the top posts of the hashtag."""
            yield from (Post(self._context, edge["node"], search_type="hashtag")
                        for edge in self._metadata("edge_hashtag_to_top_posts", "edges"))
        else:
            if next_max_id == None:
                logger.info(f"logged in here is the get_top_posts def, initialize : next_max_id = {next_max_id}")
                try:
                    """Yields the posts associated with this hashtag."""
                    self._metadata("top", "sections")
                    self._metadata("top", "next_page")
                    conn = self._metadata("top")
                    logger.info(f"next_max_id:{conn['next_max_id']}")
                except Exception as ex:
                    logger.info(ex)
                    return
                for idx, section in enumerate(conn["sections"]):
                    yield from (
                    Post(self._context, edge["media"], next_max_id=conn['next_max_id'], next_page=conn['next_page'],
                         search_type="hashtag") for edge in
                    section["layout_content"]["medias"])
            else:
                logger.info(
                    f"logged in here is the get_posts def, reinitialize : next_max_id = {next_max_id}, next_page= {next_page}")
                data = {"include_persistent": 0,
                        "page": next_page,
                        "surface": "grid",
                        "tab": "top",
                        "max_id": next_max_id}
                """Yields the posts associated with this hashtag."""
                data = self._query({"search_type": "hashtag", "post": True, 'data': data, 'name': self.name})
                conn = data["top"]
                for idx, section in enumerate(conn["sections"]):
                    yield from (Post(self._context, edge["media"], next_max_id=next_max_id, next_page=next_page,
                                     search_type="hashtag") for edge in
                                section["layout_content"]["medias"])

            while conn["next_page"]:
                data = {"include_persistent": 0,
                        "page": conn["next_page"],
                        "surface": "grid",
                        "tab": "top",
                        "max_id": conn["next_max_id"]}

                conn = self._query({"search_type": "hashtag", "post": True, 'data': data, 'name': self.name})

                logger.info(f"next_page:{conn['next_page']}")
                logger.info(f"next_max_id:{conn['next_max_id']}")
                for idx, section in enumerate(conn["sections"]):
                    yield from (
                    Post(self._context, edge["media"], next_max_id=conn['next_max_id'], next_page=conn['next_page'],
                         search_type="hashtag") for edge in
                    section["layout_content"]["medias"])

    @property
    def mediacount(self) -> int:
        """
        The count of all media associated with this hashtag.

        The number of posts with a certain hashtag may differ from the number of posts that can actually be accessed, as
        the hashtag count might include private posts
        """
        if not self._context.is_logged_in:
            logger.info("media_count")
            return self._metadata("edge_hashtag_to_media", "count")
        else:
            logger.info("media_count")
            return self._metadata("media_count")

    def get_posts(self, next_max_id=None) -> Iterator[Post]:

        if not self._context.is_logged_in:
            """Yields the posts associated with this hashtag."""
            logger.info("not logged in here is the get_posts def")
            self._metadata("edge_hashtag_to_media", "edges")
            self._metadata("edge_hashtag_to_media", "page_info")
            conn = self._metadata("edge_hashtag_to_media")

            yield from (Post(self._context, edge["node"]) for edge in conn["edges"])
            while conn["page_info"]["has_next_page"]:
                data = self._query({'__a': 1, 'max_id': conn["page_info"]["end_cursor"]})
                conn = data["edge_hashtag_to_media"]
                yield from (Post(self._context, edge["node"]) for edge in conn["edges"])
        else:
            if next_max_id == None:
                logger.info(f"logged in here is the get_posts def, initialize : next_max_id = {next_max_id}")
                """Yields the posts associated with this hashtag."""
                self._metadata("recent", "sections")
                conn = self._metadata("recent")
                logger.info(f"next_max_id:{conn['next_max_id']}")
                for idx, section in enumerate(conn["sections"]):
                    yield from (
                    Post(self._context, edge["media"], next_max_id=conn['next_max_id'], search_type="hashtag") for edge
                    in section["layout_content"]["medias"])
            else:
                logger.info(f"logged in here is the get_posts def, reinitialize : next_max_id = {next_max_id}")
                """Yields the posts associated with this hashtag."""
                data = self._query({'__a': 1, 'max_id': next_max_id})
                conn = data["recent"]
                for idx, section in enumerate(conn["sections"]):
                    yield from (Post(self._context, edge["media"], next_max_id=next_max_id, search_type="hashtag") for
                                edge in section["layout_content"]["medias"])

            while conn["next_page"]:
                data = self._query({'__a': 1, 'max_id': conn["next_max_id"]})
                conn = data["recent"]
                logger.info(f"next_max_id:{conn['next_max_id']}")
                for idx, section in enumerate(conn["sections"]):
                    yield from (
                    Post(self._context, edge["media"], next_max_id=conn['next_max_id'], search_type="hashtag") for edge
                    in section["layout_content"]["medias"])


class Profile:
    def __init__(self, context: InstabotContext, node: Dict[str, Any]):
        assert 'username' in node
        self._context = context
        self._has_public_story = None  # type: Optional[bool]
        self._node = node
        self._has_full_metadata = False
        self._iphone_struct_ = None

        if 'iphone_struct' in node:
            # if loaded from JSON with load_structure_from_file()
            self._iphone_struct_ = node['iphone_struct']

    @classmethod
    def from_username(cls, context: InstabotContext, username: str):
        """Create a Profile instance from a given username, raise exception if it does not exist.

        See also :meth:`Instaloader.check_profile_id`.

        :param context: :attr:`Instaloader.context`
        :param username: Username
        :raises: :class:`ProfileNotExistsException`
        """
        # pylint:disable=protected-access

        profile = cls(context, {'username': username.lower()})
        profile._obtain_metadata()  # to raise ProfileNotExistsException now in case username is invalid
        return profile

    @classmethod
    def from_id(cls, context: InstabotContext, profile_id: int):
        """Create a Profile instance from a given userid. If possible, use :meth:`Profile.from_username`
        or constructor directly rather than this method, since it requires more requests.

        :param context: :attr:`Instaloader.context`
        :param profile_id: userid
        :raises: :class:`ProfileNotExistsException`
        """
        if profile_id in context.profile_id_cache:
            return context.profile_id_cache[profile_id]
        data = context.graphql_query('7c16654f22c819fb63d1183034a5162f',
                                     {'user_id': str(profile_id),
                                      'include_chaining': False,
                                      'include_reel': True,
                                      'include_suggested_users': False,
                                      'include_logged_out_extras': False,
                                      'include_highlight_reels': False},
                                     rhx_gis=context.root_rhx_gis)['data']['user']
        if data:
            profile = cls(context, data['reel']['owner'])
        else:
            raise ProfileNotExistsException("No profile found, the user may have blocked you (ID: " +
                                            str(profile_id) + ").")
        context.profile_id_cache[profile_id] = profile
        return profile


    def _asdict(self):
        json_node = self._node.copy()
        # remove posts to avoid "Circular reference detected" exception
        json_node.pop('edge_media_collections', None)
        json_node.pop('edge_owner_to_timeline_media', None)
        json_node.pop('edge_saved_media', None)
        json_node.pop('edge_felix_video_timeline', None)
        if self._iphone_struct_:
            json_node['iphone_struct'] = self._iphone_struct_
        return json_node

    def _obtain_metadata(self):
        try:
            if not self._has_full_metadata:
                metadata = self._context.get_json('{}/feed/'.format(self.username), params={})
                self._node = metadata['entry_data']['ProfilePage'][0]['graphql']['user']
                self._has_full_metadata = True
        except (QueryReturnedNotFoundException, KeyError) as err:
            raise ProfileNotExistsException('Profile {} does not exist.'.format(self.username)) from err

    def _metadata(self, *keys) -> Any:
        try:
            d = self._node
            for key in keys:
                d = d[key]
            return d
        except KeyError:
            self._obtain_metadata()
            d = self._node
            for key in keys:
                d = d[key]
            return d

    @property
    def _iphone_struct(self) -> Dict[str, Any]:
        if not self._context.iphone_support:
            raise IPhoneSupportDisabledException("iPhone support is disabled.")
        if not self._context.is_logged_in:
            raise LoginRequiredException("--login required to access iPhone profile info endpoint.")
        if not self._iphone_struct_:
            data = self._context.get_iphone_json(path='api/v1/users/{}/info/'.format(self.userid), params={})
            self._iphone_struct_ = data['user']
        return self._iphone_struct_

    @property
    def to_dict(self) -> dict:
        d = {'userid': self.userid, 'username': self.username, 'full_name': self.full_name,
             'business_category_name': self.business_category_name, 'biography': self.biography,
             'external_url': self.external_url, 'profile_pic_url': self.profile_pic_url,
             'is_business_account': self.is_business_account, 'has_requested_viewer': self.has_requested_viewer,
             'is_verified': self.is_verified, 'followers': self.followers, 'followees': self.followees,
             'mediacount': self.mediacount, 'igtvcount': self.igtvcount}
        return d

    @property
    def userid(self) -> int:
        """User ID"""
        return int(self._metadata('id'))

    @property
    def username(self) -> str:
        """Profile Name"""
        return self._metadata('username').lower()

    def __hash__(self) -> int:
        return hash(self.userid)

    @property
    def is_private(self) -> bool:
        return self._metadata('is_private')

    @property
    def mediacount(self) -> int:
        return self._metadata('edge_owner_to_timeline_media', 'count')

    @property
    def igtvcount(self) -> int:
        return self._metadata('edge_felix_video_timeline', 'count')

    @property
    def followers(self) -> int:
        return self._metadata('edge_followed_by', 'count')

    @property
    def followees(self) -> int:
        return self._metadata('edge_follow', 'count')

    @property
    def external_url(self) -> Optional[str]:
        return self._metadata('external_url')

    @property
    def is_business_account(self) -> bool:

        return self._metadata('is_business_account')

    @property
    def business_category_name(self) -> str:

        return self._metadata('business_category_name')

    @property
    def biography(self) -> str:
        return self._metadata('biography')

    @property
    def full_name(self) -> str:
        return self._metadata('full_name')

    @property
    def has_requested_viewer(self) -> bool:
        return self._metadata('has_requested_viewer')

    @property
    def is_verified(self) -> bool:
        return self._metadata('is_verified')

    @property
    def requested_by_viewer(self) -> bool:
        return self._metadata('requested_by_viewer')

    @property
    def profile_pic_url(self) -> str:

        if self._context.iphone_support and self._context.is_logged_in:
            try:
                return self._iphone_struct['hd_profile_pic_url_info']['url']
            except (InstabotException, KeyError) as err:
                self._context.error('{} Unable to fetch high quality profile pic.'.format(err))
                return self._metadata("profile_pic_url_hd")
        else:
            return self._metadata("profile_pic_url_hd")

    def get_posts(self) -> NodeIterator[Post]:
        """Retrieve all posts from a profile.
        :rtype: NodeIterator[Post]"""
        self._obtain_metadata()
        return NodeIterator(
            self._context,
            '003056d32c2554def87228bc3fd9668a',
            lambda d: d['data']['user']['edge_owner_to_timeline_media'],
            lambda n: PostUserNotLogin(self._context, n, self, search_type="user"),
            {'id': self.userid},
            'https://www.instagram.com/{0}/'.format(self.username),
            self._metadata('edge_owner_to_timeline_media'),
        )

    def get_followers(self) -> NodeIterator['Profile']:
        """
        Retrieve list of followers of given profile.
        """
        if not self._context.is_logged_in:
            raise LoginRequiredException("—login required to get a profile's followers.")
        self._obtain_metadata()
        return NodeIterator(
            self._context,
            '37479f2b8209594dde7facb0d904896a',
            lambda d: d['data']['user']['edge_followed_by'],
            lambda n: Profile(self._context, n),
            {'id': str(self.userid)},
            'https://www.instagram.com/{0}/'.format(self.username),
        )
