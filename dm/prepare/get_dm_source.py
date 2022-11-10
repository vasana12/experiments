from datetime import datetime
from datetime import timedelta
from dm.log import logger
from db.model import *

from pathlib import Path
from src.utils import get_project_root
project_dir = get_project_root()


def get_source(source_type, filename):
    filepath = project_dir.joinpath("dm/source", source_type, filename)
    if source_type == "image":
        return filepath
    return filepath.read_text(encoding="utf-8")

def get_source_message(filename):
    """ get source -  message from local directory"""
    return get_source( "message", filename)

def get_source_image(filename):
    """ get source -  message from local directory"""
    return get_source("image", filename)

def get_source_hashtag(filename):
    """ get soruce - hashtag from local directory"""
    return get_source("hashtag",filename)