import enum
from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, ForeignKey, Enum, UniqueConstraint
)
from sqlalchemy.orm import relationship
from app.database import Base


class AllowTagsFromEnum(str, enum.Enum):
    EVERYONE = 'everyone'
    FOLLOWING = 'following'
    NOBODY = 'nobody'

class AllowCommentsFromEnum(str, enum.Enum):
    EVERYONE = 'everyone'
    FOLLOWING = 'following'
    FOLLOWERS = 'followers'
    BOTH = 'both'
    NOBODY = 'nobody'

class ThemeModeEnum(str, enum.Enum):
    LIGHT = 'light'
    DARK = 'dark'
    SYSTEM = 'system'

class ContentTypeEnum(str, enum.Enum):
    POST = 'post'
    CLIP = 'clip'
    STORY = 'story'


class UserSettings(Base):
    __tablename__ = "user_settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("members.id", ondelete="CASCADE"), unique=True, index=True, nullable=False)

    is_private_account = Column(Boolean, default=False)
    allow_tags_from = Column(Enum(AllowTagsFromEnum), default=AllowTagsFromEnum.EVERYONE)
    allow_mentions = Column(Boolean, default=True)
    allow_comments_from = Column(Enum(AllowCommentsFromEnum), default=AllowCommentsFromEnum.EVERYONE)
    hide_offensive_comments = Column(Boolean, default=True)
    hide_spam_comments = Column(Boolean, default=True)
    allow_sharing_to_messages = Column(Boolean, default=True)
    allow_resharing_to_stories = Column(Boolean, default=True)
    limit_interactions = Column(Boolean, default=False)
    hide_offensive_words = Column(Boolean, default=True)
    show_suggested_posts = Column(Boolean, default=True)
    hide_like_counts = Column(Boolean, default=False)
    hide_share_counts = Column(Boolean, default=False)
    data_saver = Column(Boolean, default=False)
    autoplay_wifi = Column(Boolean, default=True)
    autoplay_cellular = Column(Boolean, default=False)
    high_quality_uploads = Column(Boolean, default=True)
    save_original_photos = Column(Boolean, default=False)
    save_posted_videos = Column(Boolean, default=False)
    auto_captions = Column(Boolean, default=True)
    larger_text = Column(Boolean, default=False)
    reduce_motion = Column(Boolean, default=False)
    auto_translate = Column(Boolean, default=False)
    
    language = Column(String(50), default="English")
    theme_mode = Column(Enum(ThemeModeEnum), default=ThemeModeEnum.SYSTEM)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    user = relationship("Member", foreign_keys=[user_id])


class HiddenWord(Base):
    __tablename__ = "hidden_words"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("members.id", ondelete="CASCADE"), index=True, nullable=False)
    word = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = relationship("Member", foreign_keys=[user_id])


class BlockedAccount(Base):
    __tablename__ = "blocked_accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("members.id", ondelete="CASCADE"), index=True, nullable=False)
    blocked_user_id = Column(Integer, ForeignKey("members.id", ondelete="CASCADE"), index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (UniqueConstraint('user_id', 'blocked_user_id', name='uq_blocked_account'),)

    user = relationship("Member", foreign_keys=[user_id])
    blocked_user = relationship("Member", foreign_keys=[blocked_user_id])


class RestrictedAccount(Base):
    __tablename__ = "restricted_accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("members.id", ondelete="CASCADE"), index=True, nullable=False)
    restricted_user_id = Column(Integer, ForeignKey("members.id", ondelete="CASCADE"), index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (UniqueConstraint('user_id', 'restricted_user_id', name='uq_restricted_account'),)

    user = relationship("Member", foreign_keys=[user_id])
    restricted_user = relationship("Member", foreign_keys=[restricted_user_id])


class MutedAccount(Base):
    __tablename__ = "muted_accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("members.id", ondelete="CASCADE"), index=True, nullable=False)
    muted_user_id = Column(Integer, ForeignKey("members.id", ondelete="CASCADE"), index=True, nullable=False)
    mute_posts = Column(Boolean, default=True)
    mute_stories = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (UniqueConstraint('user_id', 'muted_user_id', name='uq_muted_account'),)

    user = relationship("Member", foreign_keys=[user_id])
    muted_user = relationship("Member", foreign_keys=[muted_user_id])


class CloseFriend(Base):
    __tablename__ = "close_friends"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("members.id", ondelete="CASCADE"), index=True, nullable=False)
    friend_user_id = Column(Integer, ForeignKey("members.id", ondelete="CASCADE"), index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (UniqueConstraint('user_id', 'friend_user_id', name='uq_close_friend'),)

    user = relationship("Member", foreign_keys=[user_id])
    friend_user = relationship("Member", foreign_keys=[friend_user_id])


class Favourite(Base):
    __tablename__ = "favourites"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("members.id", ondelete="CASCADE"), index=True, nullable=False)
    favourite_user_id = Column(Integer, ForeignKey("members.id", ondelete="CASCADE"), index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (UniqueConstraint('user_id', 'favourite_user_id', name='uq_favourite_account'),)

    user = relationship("Member", foreign_keys=[user_id])
    favourite_user = relationship("Member", foreign_keys=[favourite_user_id])


class ArchivedContent(Base):
    __tablename__ = "archived_content"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("members.id", ondelete="CASCADE"), index=True, nullable=False)
    content_id = Column(String(255), index=True, nullable=False)
    content_type = Column(Enum(ContentTypeEnum), nullable=False)
    archived_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (UniqueConstraint('user_id', 'content_id', 'content_type', name='uq_archived_content'),)

    user = relationship("Member", foreign_keys=[user_id])
