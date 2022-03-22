import copy
import json
import lzma
import random
import re
import time
import uuid
from base64 import b64decode, b64encode
from collections import namedtuple
from contextlib import suppress
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Optional, Tuple, Union
from urllib import request
import unicodedata

from . import __version__
from .exceptions import *
from .instabotcontext import InstabotContext
from .nodeiterator import NodeIterator
import logging
from .sectioniterator import SectionIterator



PostSidecarNode = namedtuple('PostSidecarNode', ['is_video', 'display_url'])
PostSidecarNode.__doc__ = "Item of a Sidecar Post."
PostSidecarNode.is_video.__doc__ = "Whether this node is a video."
PostSidecarNode.display_url.__doc__ = "URL of image or video thumbnail."

PostCommentAnswer = namedtuple('PostCommentAnswer', ['id', 'created_at_utc', 'text', 'owner', 'likes_count'])
PostCommentAnswer.id.__doc__ = "ID number of comment."
PostCommentAnswer.created_at_utc.__doc__ = ":class:`~datetime.datetime` when comment was created (UTC)."
PostCommentAnswer.text.__doc__ = "Comment text."
PostCommentAnswer.owner.__doc__ = "Owner :class:`Profile` of the comment."
PostCommentAnswer.likes_count.__doc__ = "Number of likes on comment."

PostComment = namedtuple('PostComment', (*PostCommentAnswer._fields, 'answers')) # type: ignore
for field in PostCommentAnswer._fields:
    getattr(PostComment, field).__doc__ = getattr(PostCommentAnswer, field).__doc__  # pylint: disable=no-member
PostComment.answers.__doc__ = r"Iterator which yields all :class:`PostCommentAnswer`\ s for the comment." # type: ignore

PostLocation = namedtuple('PostLocation', ['id', 'name', 'slug', 'has_public_page', 'lat', 'lng'])
PostLocation.id.__doc__ = "ID number of location."
PostLocation.name.__doc__ = "Location name."
PostLocation.slug.__doc__ = "URL friendly variant of location name."
PostLocation.has_public_page.__doc__ = "Whether location has a public page."
PostLocation.lat.__doc__ = "Latitude (:class:`float`)."
PostLocation.lng.__doc__ = "Longitude (:class:`float`)."



class Post:
    """
    Structure containing information about an Instagram post.
    """

    def __init__(self, context: InstabotContext, node: Dict[str, Any],
                 owner_profile: Optional['Profile'] = None, next_max_id:Optional = None, next_page:Optional = None, search_type = None):
        assert 'shortcode' in node or 'code' in node
        FORMAT = '%(module)s.%(funcName)s - %(message)s - %(levelname)s - %(asctime)s'
        logging.basicConfig(format=FORMAT)
        logger = logging.getLogger(__name__)
        if logger.hasHandlers():
            # Logger is already configured, remove all handlers
            logger.handlers = []
        logger.setLevel(logging.DEBUG)
        self.logger = logger
        self._context = context
        self._node = node
        self._owner_profile = owner_profile
        self._full_metadata_dict = None  # type: Optional[Dict[str, Any]]
        self._location = None            # type: Optional[PostLocation]
        self._iphone_struct_ = None

        if 'iphone_struct' in node:
            self._iphone_struct_ = node['iphone_struct']
        self.next_max_id = next_max_id
        self.next_page = next_page
        self.search_type = search_type

    @classmethod
    def from_shortcode(cls, context: InstabotContext, shortcode: str):
        """Create a post object from a given shortcode"""
        # pylint:disable=protected-access
        post = cls(context, {'shortcode': shortcode})
        post._node = post._full_metadata
        return post

    @classmethod
    def from_mediaid(cls, context: InstabotContext, mediaid: int):
        """Create a post object from a given mediaid"""
        return cls.from_shortcode(context, Post.mediaid_to_shortcode(mediaid))

    @classmethod
    def from_iphone_struct(cls, context: InstabotContext, media: Dict[str, Any]):
        """Create a post from a given iphone_struct."""
        media_types = {
            1: "GraphImage",
            2: "GraphVideo",
            8: "GraphSidecar",
        }
        fake_node = {
            "shortcode": media["code"],
            "id": media["pk"],
            "__typename": media_types[media["media_type"]],
            "is_video": media_types[media["media_type"]] == "GraphVideo",
            "date": media["taken_at"],
            "user": media["user"] if media.get("user") is not None else None,
            "location": media["location"] if media.get("location") is not None else None,
            "caption": media["caption"].get("text") if media.get("caption") is not None else None,
            "title": media.get("title"),
            "viewer_has_liked": media["has_liked"],
            "edge_media_preview_like": {"count": media["like_count"]},
            "iphone_struct": media,
        }
        with suppress(KeyError):
            fake_node["display_url"] = media['image_versions2']['candidates'][0]['url']
        with suppress(KeyError):
            fake_node["video_url"] = media['video_versions'][-1]['url']
            fake_node["video_duration"] = media["video_duration"]
            fake_node["video_view_count"] = media["view_count"]
        with suppress(KeyError):
            fake_node["edge_sidecar_to_children"] = {"edges": [{"node": {
                "display_url": node['image_versions2']['candidates'][0]['url'],
                "is_video": media_types[node["media_type"]] == "GraphVideo",
            }} for node in media["carousel_media"]]}
        return cls(context, fake_node, Profile.from_iphone_struct(context, media["user"]) if "user" in media else None)

    @staticmethod
    def shortcode_to_mediaid(code: str) -> int:
        if len(code) > 11:
            raise InvalidArgumentException("Wrong shortcode \"{0}\", unable to convert to mediaid.".format(code))
        code = 'A' * (12 - len(code)) + code
        return int.from_bytes(b64decode(code.encode(), b'-_'), 'big')

    @staticmethod
    def mediaid_to_shortcode(mediaid: int) -> str:
        if mediaid.bit_length() > 64:
            raise InvalidArgumentException("Wrong mediaid {0}, unable to convert to shortcode".format(str(mediaid)))
        return b64encode(mediaid.to_bytes(9, 'big'), b'-_').decode().replace('A', ' ').lstrip().replace(' ', 'A')

    @staticmethod
    def supported_graphql_types() -> List[str]:
        """The values of __typename fields that the :class:`Post` class can handle."""
        return ["GraphImage", "GraphVideo", "GraphSidecar"]

    def _asdict(self):
        node = self._node
        if self._full_metadata_dict:
            node.update(self._full_metadata_dict)
        if self._owner_profile:
            node['owner'] = self.owner_profile._asdict()
        if self._location:
            node['location'] = self._location._asdict()
        if self._iphone_struct_:
            node['iphone_struct'] = self._iphone_struct_
        return node

    @property
    def shortcode(self) -> str:
        """Media shortcode. URL of the post is instagram.com/p/<shortcode>/."""
        return self._node['shortcode'] if 'shortcode' in self._node else self._node['code']

    @property
    def clean_url(self) -> str:
        default_url = "https://www.instagram.com/p"
        return f"{default_url}/{self.shortcode}/"

    @property
    def mediaid(self) -> int:
        """The mediaid is a decimal representation of the media shortcode."""
        return int(self._node['id'])

    @property
    def title(self) -> Optional[str]:
        """Title of post"""
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

    @property
    def _iphone_struct(self) -> Dict[str, Any]:
        if not self._context.iphone_support:
            raise IPhoneSupportDisabledException("iPhone support is disabled.")
        if not self._context.is_logged_in:
            raise LoginRequiredException("--login required to access iPhone media info endpoint.")
        if not self._iphone_struct_:
            data = self._context.get_iphone_json(path='api/v1/media/{}/info/'.format(self.mediaid), params={})
            self._iphone_struct_ = data['items'][0]
        return self._iphone_struct_

    def _field(self, *keys) -> Any:
        """Lookups given fields in _node, and if not found in _full_metadata. Raises KeyError if not found anywhere."""
        try:
            d = self._node
            for key in keys:
                d = d[key]
            return d
        except KeyError:
            d = self._full_metadata
            for key in keys:
                d = d[key]
            return d

    @property
    def owner_profile(self) -> 'Profile':
        """:class:`Profile` instance of the Post's owner."""
        if not self._owner_profile:
            if 'username' in self._node['owner']:
                owner_struct = self._node['owner']
            else:
                # Sometimes, the 'owner' structure does not contain the username, only the user's ID.  In that case,
                # this call triggers downloading of the complete Post metadata struct, where the owner username
                # is contained.
                # Note that we cannot use Profile.from_id() here since that would lead us into a recursion.
                owner_struct = self._full_metadata['owner']
            self._owner_profile = Profile(self._context, owner_struct)
        return self._owner_profile

    @property
    def user(self):
        """user_info"""
        if self._context.is_logged_in:
            if self._iphone_struct_ is None:
                if "caption" in self._node and self._node["caption"] is not None:
                    try:
                        return self._node["caption"]["user"]
                    except:

                        return None
                elif "user" in self._node:
                    try:
                        return self._node["user"]
                    except:

                        return None
                return None

            if "caption" in self._iphone_struct_ and self._iphone_struct_["caption"] is not None:
                try:
                    return self._iphone_struct_["caption"]["user"]
                except:
                    return None
            elif "user" in self._iphone_struct_:
                try:
                    return self._iphone_struct_["user"]
                except:
                    return None
            return None

    @property
    def profile_pic_url(self):
        return self.user["profile_pic_url"]

    @property
    def owner_username(self) -> str:
        """The Post's lowercase owner name."""
        return self.owner_profile.username

    @property
    def owner_id(self) -> int:
        """The ID of the Post's owner."""
        if 'owner' in self._node and 'id' in self._node['owner']:
            return self._node['owner']['id']
        else:
            return self.owner_profile.userid

    @property
    def date_local(self):
        if self._context.is_logged_in and self.search_type != 'user':
            """Timestamp when the post was created (local time zone)."""
            try:
                return datetime.fromtimestamp(self._node["taken_at"])
            except:
                return None
        else:
            """Timestamp when the post was created (local time zone)."""
            return datetime.fromtimestamp(self._node["date"]
                                          if "date" in self._node
                                          else self._node["taken_at_timestamp"])

    @property
    def date_utc(self):
        if self._context.is_logged_in:
            """Timestamp when the post was created (UTC)."""
            try:
                return datetime.utcfromtimestamp(self._node["taken_at"])
            except:
                return None

        else:
            """Timestamp when the post was created (UTC)."""
            return datetime.utcfromtimestamp(self._node["date"]
                                             if "date" in self._node
                                             else self._node["taken_at_timestamp"])

    @property
    def date(self) -> datetime:
        """Synonym to :attr:`~Post.date_utc`"""
        return self.date_utc

    @property
    def profile(self) -> str:
        """Synonym to :attr:`~Post.owner_username`"""
        return self.owner_username

    @property
    def url(self):
        return self.contents[0]['url']

    @property
    def typename(self) -> str:
        """Type of post, GraphImage, GraphVideo or GraphSidecar"""
        return self._field('__typename')

    @property
    def mediacount(self) -> int:
        """
        The number of media in a sidecar Post, or 1 if the Post it not a sidecar.
        """
        if self.typename == 'GraphSidecar':
            edges = self._field('edge_sidecar_to_children', 'edges')
            return len(edges)
        return 1

    @property
    def contents(self):
        if not self._iphone_struct_:
            def map_select_first_image(carousel):

                carousel["image_versions2"]["candidates"] = carousel["image_versions2"]["candidates"][0]
                carousel["image_versions2"]["candidates"]["is_video"] = False
                if "accessibility_caption" in carousel["image_versions2"]["candidates"]:
                    carousel["image_versions2"]["candidates"]["accessibility_caption"] = carousel[
                        "accessibility_caption"]
                return carousel["image_versions2"]["candidates"]
            def video_node(node):
                content = {}
                if node["__typename"] == "GraphVideo":
                    content["is_video"] = node["is_video"]
                    content["url"] = node["video_url"]
                    content["video_view_count"] = node["video_view_count"]
                    content["video_duration"] = node["video_duration"] if "video_duration" in node else None
                    content["accessibility_caption"] = node[
                        "accessibility_caption"] if "accessibility_caption" in node else None
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

                            carousel_list = node['carousel_media']
                            return_contents = list(map(lambda x: map_select_first_image(x), carousel_list))

                            return return_contents
                        except Exception as e:
                            return None

                    else:
                        """one images"""

                        try:
                            if "accessibility_caption" in node:
                                node["image_versions2"]["candidates"][0]["accessibility_caption"] = node[
                                    "accessibility_caption"]
                                node["image_versions2"]["candidates"][0]["is_video"] = False

                            return [node["image_versions2"]["candidates"][0]]
                        except Exception as e:
                            return None
                else:
                    """Video"""
                    content = {}
                    content["is_video"] = True
                    content["view_count"] = self._node["view_count"]
                    content["video_codec"] = self._node["video_codec"] if "video_codec" in self._node else None
                    content["video_duration"] = self._node["video_duration"] if "video_duration" in self._node else None
                    content["width"] = self._node["video_versions"][0]["width"]
                    content["height"] = self._node["video_versions"][0]["height"]
                    content["url"] = self._node["video_versions"][0]["url"]
                    return [content]

        content_list: List[Dict] = []
        if self.typename == 'GraphSidecar':
            edges = self._field('edge_sidecar_to_children', 'edges')
            for idx, edge in enumerate(edges):
                node = edge['node']
                is_video = node['is_video']
                display_url = node['display_url']
                if not is_video and self._context.iphone_support and self._context.is_logged_in:
                    try:
                        carousel_media = self._iphone_struct['carousel_media']
                        orig_url = carousel_media[idx]['image_versions2']['candidates'][0]['url']
                        display_url = re.sub(r'([?&])se=\d+&?', r'\1', orig_url).rstrip('&')
                    except (InstabotException, KeyError, IndexError) as err:
                        self._context.error('{} Unable to fetch high quality image version of {}.'.format(
                            err, self))
                content_list.append({"is_video":is_video,"url":display_url})
            return content_list

        if self.typename == "GraphImage" and self._context.iphone_support and self._context.is_logged_in:
            try:
                orig_url = self._iphone_struct['image_versions2']['candidates'][0]['url']
                url = re.sub(r'([?&])se=\d+&?', r'\1', orig_url).rstrip('&')
                content_list.append({"is_video": False, "url": url})
                return content_list
            except (InstabotException, KeyError, IndexError) as err:
                self._context.error('{} Unable to fetch high quality image version of {}.'.format(err, self))

    def get_is_videos(self) -> List[bool]:
        """
        Return a list containing the ``is_video`` property for each media in the post.4.7
        """
        if self.typename == 'GraphSidecar':
            edges = self._field('edge_sidecar_to_children', 'edges')
            return [edge['node']['is_video'] for edge in edges]
        return [self.is_video]

    def get_sidecar_nodes(self, start=0, end=-1) -> Iterator[PostSidecarNode]:
        """
        Sidecar nodes of a Post with typename==GraphSidecar. Added parameters *start* and *end* to specify a slice of sidecar media.
        """
        if self.typename == 'GraphSidecar':
            edges = self._field('edge_sidecar_to_children', 'edges')
            if end < 0:
                end = len(edges)-1
            if start < 0:
                start = len(edges)-1

            for idx, edge in enumerate(edges):
                if start <= idx <= end:
                    node = edge['node']
                    is_video = node['is_video']
                    display_url = node['display_url']
                    if not is_video and self._context.iphone_support and self._context.is_logged_in:
                        try:
                            carousel_media = self._iphone_struct['carousel_media']
                            orig_url = carousel_media[idx]['image_versions2']['candidates'][0]['url']
                            display_url = re.sub(r'([?&])se=\d+&?', r'\1', orig_url).rstrip('&')
                        except (InstabotException, KeyError, IndexError) as err:
                            self._context.error('{} Unable to fetch high quality image version of {}.'.format(
                                err, self))
                    yield PostSidecarNode(is_video=is_video, display_url=display_url)

    def get_thumbnail(self):
        try:
            thumbnail_url = self.url
            thumbnail_img = request.urlopen(thumbnail_url).read()
        except:
            return None
        return thumbnail_img

    def get_profile_image(self):
        try:
            profile_url = self.user["profile_pic_url"]
            profile_img = request.urlopen(profile_url).read()
        except:
            return None
        return profile_img

    @property
    def caption(self) -> Optional[str]:
        if not self._iphone_struct_:
            if self._context.is_logged_in and self.search_type != 'user':
                if "caption" in self._node and self._node["caption"] is not None:
                    try:
                        caption = self._node["caption"]["text"]
                        caption = caption.replace("\n", "")
                        caption = re.sub("\s+", " ", caption)
                        caption = unicodedata.normalize('NFC', caption)
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
        """Caption."""
        caption:str = ""
        self.logger.info(self._node)
        if "edge_media_to_caption" in self._node and self._node["edge_media_to_caption"]["edges"]:
            caption = self._node["edge_media_to_caption"]["edges"][0]["node"]["text"]
        elif "caption" in self._node:
            caption = self._node["caption"]
        try:
            caption = caption.replace("\n", "")
            caption = re.sub("\s+", " ", caption)
            caption = unicodedata.normalize('NFC', caption)
        except:
            return None
        return caption

    @property
    def caption_hashtags(self) -> Optional[str]:
        """List of all lowercased hashtags (without preceeding #) that occur in the Post's caption."""
        if not self.caption:
            return None
        hashtag_regex = re.compile(r"(?:#)(\w(?:(?:\w|(?:\.(?!\.))){0,28}(?:\w))?)")
        hashtag_list = re.findall(hashtag_regex, self.caption.lower())
        hashtag_list = list(map(lambda hashtag: "#"+ hashtag ,hashtag_list))
        return ",".join(hashtag_list)

    @property
    def caption_mentions(self) -> List[str]:
        """List of all lowercased profiles that are mentioned in the Post's caption, without preceeding @."""
        if not self.caption:
            return []
        mention_regex = re.compile(r"(?:^|\W|_)(?:@)(\w(?:(?:\w|(?:\.(?!\.))){0,28}(?:\w))?)")
        return re.findall(mention_regex, self.caption.lower())

    @property
    def tagged_users(self) -> List[str]:
        """List of all lowercased users that are tagged in the Post."""
        try:
            return [edge['node']['user']['username'].lower() for edge in self._field('edge_media_to_tagged_user',
                                                                                     'edges')]
        except KeyError:
            return []

    @property
    def is_video(self) -> bool:

        """True if the Post is a video."""
        return self._node['is_video']

    @property
    def video_url(self) -> Optional[str]:

        """URL of the video, or None."""
        if self.is_video:
            version_urls = []
            try:
                version_urls.append(self._field('video_url'))
            except (InstabotException, KeyError, IndexError) as err:
                self._context.error(f"Warning: Unable to fetch video from graphql of {self}: {err}")
            if self._context.iphone_support and self._context.is_logged_in:
                try:
                    version_urls.extend(version['url'] for version in self._iphone_struct['video_versions'])
                except (InstabotException, KeyError, IndexError) as err:
                    self._context.error(f"Unable to fetch high-quality video version of {self}: {err}")
            version_urls = list(dict.fromkeys(version_urls))
            if len(version_urls) == 0:
                return None
            if len(version_urls) == 1:
                return version_urls[0]
            url_candidates: List[Tuple[int, str]] = []
            for idx, version_url in enumerate(version_urls):
                try:
                    url_candidates.append((
                        int(self._context.head(version_url, allow_redirects=True).headers.get('Content-Length', 0)),
                        version_url
                    ))
                except (InstabotException, KeyError, IndexError) as err:
                    self._context.error(f"Video URL candidate {idx+1}/{len(version_urls)} for {self}: {err}")
            if not url_candidates:
                return version_urls[0]
            url_candidates.sort()
            return url_candidates[-1][1]
        return None

    @property
    def video_view_count(self) -> Optional[int]:
        """View count of the video, or None."""
        if self.is_video:
            return self._field('video_view_count')
        return None

    @property
    def video_duration(self) -> Optional[float]:
        """Duration of the video in seconds, or None."""
        if self.is_video:
            return self._field('video_duration')
        return None

    @property
    def viewer_has_liked(self) -> Optional[bool]:
        """Whether the viewer has liked the post, or None if not logged in."""
        if not self._context.is_logged_in:
            return None
        if 'likes' in self._node and 'viewer_has_liked' in self._node['likes']:
            return self._node['likes']['viewer_has_liked']
        return self._field('viewer_has_liked')

    @property
    def likes(self) -> int:
        if not self._iphone_struct_:
            if self._context.is_logged_in and self.search_type != 'user':
                """Likes count"""
                if "like_count" in self._node:
                    try:
                        return self._node["like_count"]
                    except:
                        return 0
            else:
                if "edge_media_preview_like" in self._node:
                    try:
                        return self._field('edge_media_preview_like', 'count')
                    except:
                        return 0
                return 0

        """Likes count"""
        try:
            if "like_count" in self._iphone_struct_.keys():
                return self._iphone_struct_.get('like_count')
            else:
                self.logger.debug(f"shortcode:{self.shortcode} like_count error return 0")
                return 0
        except Exception as e:
            self.logger.debug(f"shortcode:{self.shortcode} like_count error")
            pass
        return self._field('edge_media_preview_like', 'count')

    @property
    def comments(self) -> int:
        """Comment count including answers"""
        if not self._iphone_struct_:
            if self._context.is_logged_in and self.search_type != "user":
                """Comment count including answers"""
                try:
                    return self._node["comment_count"]
                except KeyError:
                    return 0
            else:
                """Comment count including answers"""
                # If the count is already present in `self._node`, do not use `self._field` which could trigger fetching the
                # full metadata dict.
                comments = self._node.get('edge_media_to_comment')
                if comments and 'count' in comments:
                    return comments['count']
                try:
                    return self._field('edge_media_to_parent_comment', 'count')
                except KeyError:
                    return self._field('edge_media_to_comment', 'count')
        try:
            if "comment_count" in self._iphone_struct_.keys():
                return self._iphone_struct_.get('comment_count')
            else:
                self.logger.error(f"shortcode:{self.shortcode} comments error return 0")
                return 0
        except Exception as e:
            self.logger.error(f"shortcode:{self.shortcode} comments error")
            pass
        # comments = self._node.get('edge_media_to_comment')
        # if comments and 'count' in comments:
        #     return comments['count']
        # try:
        #     return self._field('edge_media_to_parent_comment', 'count')
        # except KeyError:
        #     return self._field('edge_media_to_comment', 'count')

    def get_comments(self) -> Iterable[PostComment]:
        r"""Iterate over all comments of the post."""
        def _postcommentanswer(node):
            return PostCommentAnswer(id=int(node['id']),
                                     created_at_utc=datetime.utcfromtimestamp(node['created_at']),
                                     text=node['text'],
                                     owner=Profile(self._context, node['owner']),
                                     likes_count=node.get('edge_liked_by', {}).get('count', 0))

        def _postcommentanswers(node):
            if 'edge_threaded_comments' not in node:
                return
            answer_count = node['edge_threaded_comments']['count']
            if answer_count == 0:
                return
            answer_edges = node['edge_threaded_comments']['edges']
            if answer_count == len(answer_edges):
                yield from (_postcommentanswer(comment['node']) for comment in answer_edges)
                return
            yield from NodeIterator(
                self._context,
                '51fdd02b67508306ad4484ff574a0b62',
                lambda d: d['data']['comment']['edge_threaded_comments'],
                _postcommentanswer,
                {'comment_id': node['id']},
                'https://www.instagram.com/p/{0}/'.format(self.shortcode),
            )

        def _postcomment(node):
            return PostComment(*_postcommentanswer(node),
                               answers=_postcommentanswers(node))
        if self.comments == 0:
            # Avoid doing additional requests if there are no comments
            return []

        comment_edges = self._field('edge_media_to_comment', 'edges')
        answers_count = sum([edge['node'].get('edge_threaded_comments', {}).get('count', 0) for edge in comment_edges])

        if self.comments == len(comment_edges) + answers_count:
            # If the Post's metadata already contains all parent comments, don't do GraphQL requests to obtain them
            return [_postcomment(comment['node']) for comment in comment_edges]
        return NodeIterator(
            self._context,
            '97b41c52301f77ce508f55e66d17620e',
            lambda d: d['data']['shortcode_media']['edge_media_to_parent_comment'],
            _postcomment,
            {'shortcode': self.shortcode},
            'https://www.instagram.com/p/{0}/'.format(self.shortcode),
        )

    def get_likes(self) -> Iterator['Profile']:
        """
        Iterate over all likes of the post. A :class:`Profile` instance of each likee is yielded.
           Require being logged in (as required by Instagram).
        """
        if not self._context.is_logged_in:
            raise LoginRequiredException("--login required to access likes of a post.")
        if self.likes == 0:
            # Avoid doing additional requests if there are no comments
            return
        likes_edges = self._field('edge_media_preview_like', 'edges')
        if self.likes == len(likes_edges):
            # If the Post's metadata already contains all likes, don't do GraphQL requests to obtain them
            yield from (Profile(self._context, like['node']) for like in likes_edges)
            return
        yield from NodeIterator(
            self._context,
            '1cb6ec562846122743b61e492c85999f',
            lambda d: d['data']['shortcode_media']['edge_liked_by'],
            lambda n: Profile(self._context, n),
            {'shortcode': self.shortcode},
            'https://www.instagram.com/p/{0}/'.format(self.shortcode),
        )

    @property
    def is_sponsored(self) -> bool:
        """
        Whether Post is a sponsored post, equivalent to non-empty :meth:`Post.sponsor_users`."""
        try:
            sponsor_edges = self._field('edge_media_to_sponsor_user', 'edges')
        except KeyError:
            return False
        return bool(sponsor_edges)

    @property
    def sponsor_users(self) -> List['Profile']:
        """
        The Post's sponsors.
        """
        return ([] if not self.is_sponsored else
                [Profile(self._context, edge['node']['sponsor']) for edge in
                 self._field('edge_media_to_sponsor_user', 'edges')])

    @property
    def location(self) -> Optional[Dict]:
        """
        # If the Post has a location, dictionary with fields 'id', 'lat' and 'lng' and 'name'.
        #
        #    Require being logged in (as required by Instagram), return None if not logged-in.
        # """
        """
         If the Post has a location, returns PostLocation namedtuple with fields 'id', 'lat' and 'lng' and 'name'.

         .. versionchanged:: 4.2.9
            Require being logged in (as required by Instagram), return None if not logged-in.
         """
        try:
            location = self._node["location"]
            return location
        except:
            return None

class Profile:
    """
    An Instagram Profile.
    """

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

        :param context: :attr:`Instabot.context`
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

    @classmethod
    def from_iphone_struct(cls, context: InstabotContext, media: Dict[str, Any]):
        """Create a profile from a given iphone_struct."""
        return cls(context, {
            "id": media["pk"],
            "username": media["username"],
            "is_private": media["is_private"],
            "full_name": media["full_name"],
            "profile_pic_url_hd": media["profile_pic_url"],
            "iphone_struct": media,
        })
    @classmethod
    def own_profile(cls, context: InstabotContext):
        """Return own profile if logged-in."""
        if not context.is_logged_in:
            raise LoginRequiredException("--login required to access own profile.")
        return cls(context, context.graphql_query("d6f4427fbe92d846298cf93df0b937d3", {})["data"]["user"])

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
    def userid(self) -> int:
        """User ID"""
        return int(self._metadata('id'))

    @property
    def username(self) -> str:
        """Profile Name"""
        return self._metadata('username').lower()

    def __repr__(self):
        return '<Profile {} ({})>'.format(self.username, self.userid)

    def __eq__(self, o: object) -> bool:
        if isinstance(o, Profile):
            return self.userid == o.userid
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self.userid)

    @property
    def is_private(self) -> bool:
        return self._metadata('is_private')

    @property
    def followed_by_viewer(self) -> bool:
        return self._metadata('followed_by_viewer')

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
    def blocked_by_viewer(self) -> bool:
        return self._metadata('blocked_by_viewer')

    @property
    def follows_viewer(self) -> bool:
        return self._metadata('follows_viewer')

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

    def get_profile_pic_url(self) -> str:
        return self.profile_pic_url

    def get_posts(self) -> NodeIterator[Post]:
        """Retrieve all posts from a profile.
        :rtype: NodeIterator[Post]"""
        self._obtain_metadata()
        return NodeIterator(
            self._context,
            '003056d32c2554def87228bc3fd9668a',
            lambda d: d['data']['user']['edge_owner_to_timeline_media'],
            lambda n: Post(self._context, n, self),
            {'id': self.userid},
            'https://www.instagram.com/{0}/'.format(self.username),
            self._metadata('edge_owner_to_timeline_media'),
        )



    def get_igtv_posts(self) -> NodeIterator[Post]:
        """Retrieve all IGTV posts."""
        self._obtain_metadata()
        return NodeIterator(
            self._context,
            'bc78b344a68ed16dd5d7f264681c4c76',
            lambda d: d['data']['user']['edge_felix_video_timeline'],
            lambda n: Post(self._context, n, self),
            {'id': self.userid},
            'https://www.instagram.com/{0}/channel/'.format(self.username),
            self._metadata('edge_felix_video_timeline'),
        )

    def get_followers(self) -> NodeIterator['Profile']:
        """
        Retrieve list of followers of given profile.
        To use this, one needs to be logged in and private profiles has to be followed.
        """
        if not self._context.is_logged_in:
            raise LoginRequiredException("--login required to get a profile's followers.")
        self._obtain_metadata()
        return NodeIterator(
            self._context,
            '37479f2b8209594dde7facb0d904896a',
            lambda d: d['data']['user']['edge_followed_by'],
            lambda n: Profile(self._context, n),
            {'id': str(self.userid)},
            'https://www.instagram.com/{0}/'.format(self.username),
        )

    def get_followees(self) -> NodeIterator['Profile']:
        """
        Retrieve list of followees (followings) of given profile.
        To use this, one needs to be logged in and private profiles has to be followed.
        """
        if not self._context.is_logged_in:
            raise LoginRequiredException("--login required to get a profile's followees.")
        self._obtain_metadata()
        return NodeIterator(
            self._context,
            '58712303d941c6855d4e888c5f0cd22f',
            lambda d: d['data']['user']['edge_follow'],
            lambda n: Profile(self._context, n),
            {'id': str(self.userid)},
            'https://www.instagram.com/{0}/'.format(self.username),
        )

    def get_similar_accounts(self) -> Iterator['Profile']:
        """
        Retrieve list of suggested / similar accounts for this profile.
        To use this, one needs to be logged in.
        """
        if not self._context.is_logged_in:
            raise LoginRequiredException("--login required to get a profile's similar accounts.")
        self._obtain_metadata()
        yield from (Profile(self._context, edge["node"]) for edge in
                    self._context.graphql_query("ad99dd9d3646cc3c0dda65debcd266a7",
                                                {"user_id": str(self.userid), "include_chaining": True},
                                                "https://www.instagram.com/{0}/"
                                                .format(self.username))["data"]["user"]["edge_chaining"]["edges"])


class Hashtag:
    def __init__(self, context: InstabotContext, node: Dict[str, Any]):
        self._context = context
        self._node = node
        self._has_full_metadata = False

    @classmethod
    def from_name(cls, context: InstabotContext, name: str):
        hashtag = cls(context, {'name': name.lower()})
        hashtag._obtain_metadata()
        return hashtag
    @property
    def name(self):
        """Hashtag name lowercased"""
        return self._node["name"].lower()

    def _query(self, params):
        json_response = self._context.get_json("explore/tags/{0}/".format(self.name), params)
        return json_response["graphql"]["hashtag"] if "graphql" in json_response else json_response["data"]

    def _query_api_v3(self, params):

        json_response = self._context.get_json_v_api("explore/tags/{0}/".format(self.name), params)
        print(f"json_response_test:{json_response}")
        return json_response["graphql"]["hashtag"] if "graphql" in json_response else json_response["data"]


    def _obtain_metadata(self):
        if not self._has_full_metadata:
            self._node = self._query({"__a": 1})
            self._has_full_metadata = True

    def _asdict(self):
        json_node = self._node.copy()
        # remove posts
        json_node.pop("edge_hashtag_to_top_posts", None)
        json_node.pop("edge_hashtag_to_media", None)
        return json_node


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

    @property
    def mediacount(self) -> int:
        """
        The count of all media associated with this hashtag.

        The number of posts with a certain hashtag may differ from the number of posts that can actually be accessed, as
        the hashtag count might include private posts
        """
        if not self._context.is_logged_in:
            return self._metadata("edge_hashtag_to_media", "count")
        else:
            return self._metadata("media_count")

    def get_top_posts_api_v3(self, next_max_id=None, next_page=None) -> Iterator[Post]:
        """Yields the top posts of the hashtag. version api-v3"""

        if next_max_id == None:
            self._context.logger.info(f"logged in here is the get_top_posts def, initialize : next_max_id = {next_max_id}")
            """Yields the posts associated with this hashtag."""
            self._metadata("top", "sections")
            conn = self._metadata("top")
            print(conn)
            self._context.logger.info(f"next_max_id:{conn['next_max_id']}")
            for idx, section in enumerate(conn["sections"]):
                yield from (
                Post(self._context, edge["media"], next_max_id=conn['next_max_id'], next_page=conn['next_page'],
                     search_type="hashtag") for edge in
                section["layout_content"]["medias"])

        else:
            self._context.logger.info(
                f"logged in here is the get_posts def, reinitialize : next_max_id = {next_max_id}, next_page= {next_page}")
            data = {"include_persistent": 0,
                    "page": next_page,
                    "surface": "grid",
                    "tab": "top",
                    "max_id": next_max_id}
            """Yields the posts associated with this hashtag."""
            data = self._query_api_v3({"search_type": "hashtag", "post": True, 'data': data, 'name': self.name})
            conn = data["top"]
            for idx, section in enumerate(conn["sections"]):
                yield from (
                Post(self._context, edge["media"], next_max_id=next_max_id, next_page=next_page, search_type="hashtag")
                for edge in
                section["layout_content"]["medias"])

        while conn["next_page"]:
            data = {"include_persistent": 0,
                    "page": conn["next_page"],
                    "surface": "grid",
                    "tab": "top",
                    "max_id": conn["next_max_id"]}

            conn = self._query_api_v3({"search_type": "hashtag", "post": True, 'data': data, 'name': self.name})

            self._context.logger.info(f"next_page:{conn['next_page']}")
            self._context.logger.info(f"next_max_id:{conn['next_max_id']}")
            for idx, section in enumerate(conn["sections"]):
                yield from (
                Post(self._context, edge["media"], next_max_id=conn['next_max_id'], next_page=conn['next_page'],
                     search_type="hashtag") for edge in
                section["layout_content"]["medias"])

    def get_posts_api_v3(self, next_max_id=None, next_page=None) -> Iterator[Post]:

        if not self._context.is_logged_in:
            """Yields the posts associated with this hashtag."""
            self._context.logger.info("not logged in here is the get_posts def")
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
                self._context.logger.info(f"logged in here is the get_posts def, initialize : next_max_id = {next_max_id}")
                """Yields the posts associated with this hashtag."""
                self._metadata("recent", "sections")
                conn = self._metadata("recent")
                self._context.logger.info(f"next_max_id:{conn['next_max_id']}")
                for idx, section in enumerate(conn["sections"]):
                    yield from (
                    Post(self._context, edge["media"], next_max_id=conn['next_max_id'], next_page=conn['next_page'],
                         search_type="hashtag") for edge in
                    section["layout_content"]["medias"])
            else:
                self._context.logger.info(
                    f"logged in here is the get_posts def, reinitialize : next_max_id = {next_max_id}, next_page= {next_page}")
                data = {"include_persistent": 0,
                        "page": next_page,
                        "surface": "grid",
                        "tab": "recent",
                        "max_id": next_max_id}
                """Yields the posts associated with this hashtag."""
                data = self._query_api_v3({"search_type": "hashtag", "post": True, 'data': data, 'name': self.name})
                conn = data["recent"]
                for idx, section in enumerate(conn["sections"]):
                    yield from (Post(self._context, edge["media"], next_max_id=next_max_id, next_page=next_page,
                                     search_type="hashtag") for edge in
                                section["layout_content"]["medias"])

            while conn["next_page"]:
                data = {"include_persistent": 0,
                        "page": conn["next_page"],
                        "surface": "grid",
                        "tab": "recent",
                        "max_id": conn["next_max_id"]}

                conn = self._query_api_v3({"search_type": "hashtag", "post": True, 'data': data, 'name': self.name})

                self._context.logger.info(f"next_page:{conn['next_page']}")
                self._context.logger.info(f"next_max_id:{conn['next_max_id']}")
                for idx, section in enumerate(conn["sections"]):
                    yield from (
                        Post(self._context, edge["media"], next_max_id=conn['next_max_id'], next_page=conn['next_page'],
                             search_type="hashtag") for edge in
                        section["layout_content"]["medias"])

    def get_recent_posts(self) -> Iterator[Post]:
        """Yields the top posts of the hashtag."""
        try:
            yield from (Post(self._context, edge["node"])
                        for edge in self._metadata("edge_hashtag_to_top_posts", "edges"))
        except KeyError:
            yield from SectionIterator(
                self._context,
                lambda d: d["data"]["recent"],
                lambda m: Post.from_iphone_struct(self._context, m),
                f"explore/tags/{self.name}/",
                self._metadata("recent"),
            )

    def get_top_posts(self) -> Iterator[Post]:
        """Yields the top posts of the hashtag."""
        try:
            yield from (Post(self._context, edge["node"])
                        for edge in self._metadata("edge_hashtag_to_top_posts", "edges"))
        except KeyError:
            yield from SectionIterator(
                self._context,
                lambda d: d["data"]["top"],
                lambda m: Post.from_iphone_struct(self._context, m),
                f"explore/tags/{self.name}/",
                self._metadata("top"),
            )



    def get_all_posts(self) -> Iterator[Post]:
        """Yields all posts"""
        sorted_top_posts = iter(sorted(self.get_top_posts(), key=lambda p: p.date_utc, reverse=True))
        other_posts = self.get_recent_posts()
        next_top = next(sorted_top_posts, None)
        next_other = next(other_posts, None)
        while next_top is not None or next_other is not None:
            if next_other is None:
                assert next_top is not None
                yield next_top
                yield from sorted_top_posts
                break
            if next_top is None:
                assert next_other is not None
                yield next_other
                yield from other_posts
                break
            if next_top == next_other:
                yield next_top
                next_top = next(sorted_top_posts, None)
                next_other = next(other_posts, None)
                continue
            if next_top.date_utc > next_other.date_utc:
                yield next_top
                next_top = next(sorted_top_posts, None)
            else:
                yield next_other
                next_other = next(other_posts, None)


