from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime
from app.models.settings import AllowTagsFromEnum, AllowCommentsFromEnum, ThemeModeEnum, ContentTypeEnum

class UserSettingsBase(BaseModel):
    is_private_account: Optional[bool] = None
    allow_tags_from: Optional[AllowTagsFromEnum] = None
    allow_mentions: Optional[bool] = None
    allow_comments_from: Optional[AllowCommentsFromEnum] = None
    hide_offensive_comments: Optional[bool] = None
    hide_spam_comments: Optional[bool] = None
    allow_sharing_to_messages: Optional[bool] = None
    allow_resharing_to_stories: Optional[bool] = None
    limit_interactions: Optional[bool] = None
    hide_offensive_words: Optional[bool] = None
    show_suggested_posts: Optional[bool] = None
    hide_like_counts: Optional[bool] = None
    hide_share_counts: Optional[bool] = None
    data_saver: Optional[bool] = None
    autoplay_wifi: Optional[bool] = None
    autoplay_cellular: Optional[bool] = None
    high_quality_uploads: Optional[bool] = None
    save_original_photos: Optional[bool] = None
    save_posted_videos: Optional[bool] = None
    auto_captions: Optional[bool] = None
    larger_text: Optional[bool] = None
    reduce_motion: Optional[bool] = None
    auto_translate: Optional[bool] = None
    language: Optional[str] = None
    theme_mode: Optional[ThemeModeEnum] = None

class UserSettingsUpdate(UserSettingsBase):
    pass

class UserSettingsResponse(UserSettingsBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class HiddenWordCreate(BaseModel):
    word: str

class HiddenWordResponse(BaseModel):
    id: int
    user_id: int
    word: str
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class ConnectionResponse(BaseModel):
    id: int
    full_name: str
    username: str
    avatar_url: Optional[str] = None

class MutedConnectionResponse(ConnectionResponse):
    mute_posts: bool = True
    mute_stories: bool = True

class ArchivedContentCreate(BaseModel):
    content_id: str
    content_type: ContentTypeEnum

class ArchivedContentResponse(BaseModel):
    id: int
    user_id: int
    content_id: str
    content_type: ContentTypeEnum
    archived_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
