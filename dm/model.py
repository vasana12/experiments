from datetime import datetime, timedelta
from typing import List, Optional
from enum import Enum
from pydantic import BaseModel, FilePath, HttpUrl, ValidationError, validator, Field


class Project(BaseModel):
    name: str
    text_file_name: str
    start_date: Optional[datetime] = None
    exclude_project_name: Optional[str] = None
    exclude_project_start_date: Optional[str] = None
    exclude_project_end_date: Optional[str] = None

    @validator('exclude_project_name', always=True)
    def set_exclude_project_name(cls, v, values, **kwargs):
        return v or values["name"]

    @validator('start_date', always=True, pre=True)
    def set_start_date(cls, v, values, **kwargs):
        if type(v) is str:
            return datetime.strptime(v, "%Y-%m-%d")
        if v is None:
            return datetime.now()
        if type(v) is datetime:
            return v
        else:
            raise ValidationError

    @validator('exclude_project_start_date', always=True)
    def set_exclude_project_start_date(cls, v, values, **kwargs):
        start_date = datetime.now().date() - timedelta(days=365)
        return v or start_date.strftime("%Y-%m-%d")

    @validator('exclude_project_end_date', always=True)
    def set_exclude_project_end_date(cls, v, values, **kwargs):
        end_date = datetime.now().date()
        return v or end_date.strftime("%Y-%m-%d")

class Task(BaseModel):
    project: Project
    search_hashtag: List
    exclude_hashtag: Optional[List]
    user_followed_by_gte: Optional[int] = None
    user_followed_by_lte: Optional[int] = None
    user_follow_by_gte: Optional[int] = None
    user_follow_by_lte: Optional[int] = None
    avg_like_gte: Optional[int] = None
    size: Optional[int] = None
    spam_filter: Optional[bool] = None
    _schema_version: str = "1.0"


    @validator('user_followed_by_gte', always=True)
    def set_user_followed_by_gte(cls, v, values, **kwargs):
        return v or 0

    @validator('user_followed_by_lte', always=True)
    def set_user_followed_by_lte(cls, v, values, **kwargs):
        return v or 99999999

    @validator('user_follow_by_gte', always=True)
    def set_user_follow_by_gte(cls, v, values, **kwargs):
        return v or 0

    @validator('user_follow_by_lte', always=True)
    def set_user_follow_by_lte(cls, v, values, **kwargs):
        return v or 99999999

    @validator('avg_like_gte', always=True)
    def set_avg_like_gte(cls, v, values, **kwargs):
        return v or 0

    @validator('size', always=True)
    def set_size(cls, v, values, **kwargs):
        return v or 1000

    @validator('spam_filter', always=True)
    def set_spam_filter(cls, v, values, **kwargs):
        return v or False