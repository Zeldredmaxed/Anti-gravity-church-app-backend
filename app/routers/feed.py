"""Feed router: posts, likes, comments."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.models.feed import Post, PostLike, PostComment
from app.models.user import User
from app.schemas.feed import (
    PostCreate, PostUpdate, PostResponse, PostDetailResponse,
    CommentCreate, CommentResponse,
)
from app.utils.security import get_current_user, require_role
from app.utils.mentions import process_mentions

router = APIRouter(prefix="/feed", tags=["Feed & Social"])


def _post_response(p, author_name=None, is_liked=False):
    return PostResponse(
        id=p.id, church_id=p.church_id, author_id=p.author_id,
        author_name=author_name, content=p.content, media_urls=p.media_urls or [],
        post_type=p.post_type, visibility=p.visibility,
        likes_count=p.likes_count, comments_count=p.comments_count,
        shares_count=p.shares_count, is_pinned=p.is_pinned,
        is_liked_by_me=is_liked, created_at=p.created_at, updated_at=p.updated_at)


@router.get("", response_model=list[PostResponse])
async def get_feed(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    post_type: str = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)):
    """Get church feed. Pinned posts always appear first."""
    query = select(Post).where(
        Post.church_id == current_user.church_id,
        Post.is_deleted == False)

    # Visibility filter based on role
    if current_user.role in ("admin", "pastor"):
        pass  # See everything
    elif current_user.role in ("staff", "volunteer"):
        query = query.where(Post.visibility.in_(["public", "members_only"]))
    else:
        query = query.where(Post.visibility.in_(["public", "members_only"]))

    if post_type:
        query = query.where(Post.post_type == post_type)

    # Pinned first, then by date
    query = query.order_by(Post.is_pinned.desc(), Post.created_at.desc())
    query = query.offset(offset).limit(limit)

    posts = (await db.execute(query)).scalars().all()
    items = []
    for p in posts:
        author = (await db.execute(select(User).where(User.id == p.author_id))).scalar_one_or_none()
        is_liked = (await db.execute(select(PostLike).where(
            PostLike.post_id == p.id, PostLike.user_id == current_user.id
        ))).scalar_one_or_none() is not None
        items.append(_post_response(p, author.full_name if author else None, is_liked))
    return items


@router.post("/posts", response_model=PostResponse, status_code=201)
async def create_post(
    data: PostCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)):
    """Create a new post in the church feed."""
    # Only admins/pastors can make announcements or pin
    if data.post_type == "announcement" and current_user.role not in ("admin", "pastor"):
        raise HTTPException(status_code=403, detail="Only pastors can create announcements")
    if data.visibility == "leaders_only" and current_user.role not in ("admin", "pastor", "staff"):
        raise HTTPException(status_code=403, detail="Cannot create leaders-only posts")

    post = Post(
        church_id=current_user.church_id, author_id=current_user.id,
        content=data.content, media_urls=data.media_urls or [],
        post_type=data.post_type, visibility=data.visibility,
    )
    db.add(post)
    await db.flush()
    await db.refresh(post)
    await process_mentions(db, post.content, current_user.id, "post", post.id)
    return _post_response(post, current_user.full_name, False)


@router.get("/posts/{post_id}", response_model=PostDetailResponse)
async def get_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)):
    """Get a single post with comments."""
    p = (await db.execute(select(Post).where(
        Post.id == post_id, Post.church_id == current_user.church_id,
        Post.is_deleted == False
    ))).scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Post not found")

    author = (await db.execute(select(User).where(User.id == p.author_id))).scalar_one_or_none()
    is_liked = (await db.execute(select(PostLike).where(
        PostLike.post_id == p.id, PostLike.user_id == current_user.id
    ))).scalar_one_or_none() is not None

    # Get top-level comments
    top_comments = (await db.execute(
        select(PostComment).where(
            PostComment.post_id == post_id,
            PostComment.parent_id.is_(None),
            PostComment.is_deleted == False)
        .order_by(PostComment.created_at)
    )).scalars().all()

    comments = []
    for c in top_comments:
        c_author = (await db.execute(select(User).where(User.id == c.author_id))).scalar_one_or_none()
        # Get replies
        reply_rows = (await db.execute(
            select(PostComment).where(PostComment.parent_id == c.id, PostComment.is_deleted == False)
            .order_by(PostComment.created_at)
        )).scalars().all()
        replies = []
        for r in reply_rows:
            r_author = (await db.execute(select(User).where(User.id == r.author_id))).scalar_one_or_none()
            replies.append(CommentResponse(
                id=r.id, post_id=r.post_id, author_id=r.author_id,
                author_name=r_author.full_name if r_author else None,
                content=r.content, parent_id=r.parent_id,
                is_deleted=r.is_deleted, created_at=r.created_at))
        comments.append(CommentResponse(
            id=c.id, post_id=c.post_id, author_id=c.author_id,
            author_name=c_author.full_name if c_author else None,
            content=c.content, parent_id=c.parent_id,
            is_deleted=c.is_deleted, created_at=c.created_at, replies=replies))

    resp = _post_response(p, author.full_name if author else None, is_liked)
    return PostDetailResponse(**resp.model_dump(), comments=comments)


@router.put("/posts/{post_id}", response_model=PostResponse)
async def update_post(
    post_id: int, data: PostUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)):
    p = (await db.execute(select(Post).where(
        Post.id == post_id, Post.church_id == current_user.church_id
    ))).scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Post not found")
    if p.author_id != current_user.id and current_user.role not in ("admin", "pastor"):
        raise HTTPException(status_code=403, detail="Cannot edit this post")

    # Only admin/pastor can pin
    if data.is_pinned is not None and current_user.role not in ("admin", "pastor"):
        raise HTTPException(status_code=403, detail="Only pastors can pin posts")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(p, field, value)
    db.add(p)
    await db.flush()
    await db.refresh(p)
    return _post_response(p)


@router.delete("/posts/{post_id}", status_code=204)
async def delete_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)):
    p = (await db.execute(select(Post).where(
        Post.id == post_id, Post.church_id == current_user.church_id
    ))).scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Post not found")
    if p.author_id != current_user.id and current_user.role not in ("admin", "pastor"):
        raise HTTPException(status_code=403, detail="Cannot delete this post")
    p.is_deleted = True
    db.add(p)


@router.post("/posts/{post_id}/share", status_code=200)
async def share_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)):
    """Share a post."""
    p = (await db.execute(select(Post).where(
        Post.id == post_id, Post.church_id == current_user.church_id
    ))).scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Post not found")
    
    p.shares_count = (p.shares_count or 0) + 1
    db.add(p)
    await db.flush()
    
    # Mock deep-link URL
    share_url = f"https://app.church.com/p/{post_id}"
    return {"message": "Post shared", "shares_count": p.shares_count, "share_url": share_url}


# --- Likes ---

@router.post("/posts/{post_id}/like", status_code=201)
async def like_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)):
    p = (await db.execute(select(Post).where(
        Post.id == post_id, Post.church_id == current_user.church_id
    ))).scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Post not found")

    existing = (await db.execute(select(PostLike).where(
        PostLike.post_id == post_id, PostLike.user_id == current_user.id
    ))).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Already liked")

    like = PostLike(post_id=post_id, user_id=current_user.id)
    db.add(like)
    p.likes_count = (p.likes_count or 0) + 1
    db.add(p)
    await db.flush()
    return {"message": "Liked", "likes_count": p.likes_count}


@router.delete("/posts/{post_id}/like", status_code=200)
async def unlike_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)):
    existing = (await db.execute(select(PostLike).where(
        PostLike.post_id == post_id, PostLike.user_id == current_user.id
    ))).scalar_one_or_none()
    if not existing:
        raise HTTPException(status_code=400, detail="Not liked")
    await db.delete(existing)

    p = (await db.execute(select(Post).where(Post.id == post_id))).scalar_one_or_none()
    if p:
        p.likes_count = max((p.likes_count or 0) - 1, 0)
        db.add(p)
    return {"message": "Unliked", "likes_count": p.likes_count if p else 0}


# --- Comments ---

@router.post("/posts/{post_id}/comments", response_model=CommentResponse, status_code=201)
async def add_comment(
    post_id: int, data: CommentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)):
    p = (await db.execute(select(Post).where(
        Post.id == post_id, Post.church_id == current_user.church_id
    ))).scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Post not found")

    comment = PostComment(
        post_id=post_id, author_id=current_user.id,
        content=data.content, parent_id=data.parent_id,
    )
    db.add(comment)
    p.comments_count = (p.comments_count or 0) + 1
    db.add(p)
    await db.flush()
    await db.refresh(comment)
    
    await process_mentions(db, comment.content, current_user.id, "post_comment", comment.id)

    return CommentResponse(
        id=comment.id, post_id=comment.post_id, author_id=comment.author_id,
        author_name=current_user.full_name, content=comment.content,
        parent_id=comment.parent_id, is_deleted=False,
        created_at=comment.created_at)


@router.delete("/posts/{post_id}/comments/{comment_id}", status_code=204)
async def delete_comment(
    post_id: int, comment_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)):
    c = (await db.execute(select(PostComment).where(
        PostComment.id == comment_id, PostComment.post_id == post_id
    ))).scalar_one_or_none()
    if not c:
        raise HTTPException(status_code=404, detail="Comment not found")
    if c.author_id != current_user.id and current_user.role not in ("admin", "pastor"):
        raise HTTPException(status_code=403, detail="Cannot delete this comment")
    c.is_deleted = True
    c.content = "[Comment deleted]"
    db.add(c)
