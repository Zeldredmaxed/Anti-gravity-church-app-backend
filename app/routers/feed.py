"""Feed router: posts, likes, comments — aligned with frontend audit."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.models.feed import Post, PostAmen, PostComment
from app.models.social import FlockMember
from app.models.user import User
from app.schemas.feed import (
    PostCreate, PostUpdate, PostResponse, PostDetailResponse,
    CommentCreate, CommentResponse,
)
from app.utils.security import get_current_user, require_role
from app.utils.mentions import process_mentions

router = APIRouter(prefix="/feed", tags=["Feed & Social"])


def _post_response(p, author_name=None, author_avatar=None, is_amened=False):
    return {
        "id": p.id,
        "church_id": p.church_id,
        "author_id": p.author_id,
        "author_name": author_name,
        "author_avatar": author_avatar,
        "content": p.content,
        "media_urls": p.media_urls or [],
        "image_url": (p.media_urls or [None])[0] if p.media_urls else None,
        "post_type": p.post_type,
        "visibility": p.visibility,
        "like_count": p.amen_count or 0,
        "amen_count": p.amen_count or 0,
        "comment_count": p.comments_count or 0,
        "comments_count": p.comments_count or 0,
        "share_count": p.shares_count or 0,
        "shares_count": p.shares_count or 0,
        "is_pinned": p.is_pinned or False,
        "is_liked": is_amened,
        "is_amened_by_me": is_amened,
        "created_at": p.created_at.isoformat() if p.created_at else None,
        "updated_at": p.updated_at.isoformat() if p.updated_at else None,
    }


# ── GET /feed ──────────────────────────────────────────────────────
@router.get("")
async def get_feed(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    post_type: str = Query(None),
    author_id: int = Query(None),
    filter: str = Query(None),          # "following" or "favourites"
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get church feed. Supports ?author_id, ?filter=following|favourites."""
    query = select(Post).where(Post.is_deleted == False)

    # By default scope to church — unless seeking cross-church following feed
    if filter != "following":
        query = query.where(Post.church_id == current_user.church_id)

    # Visibility
    if current_user.role not in ("admin", "pastor"):
        query = query.where(Post.visibility.in_(["public", "members_only", "all"]))

    if author_id:
        query = query.where(Post.author_id == author_id)

    if filter == "following":
        followed_ids = (await db.execute(
            select(FlockMember.followed_id).where(FlockMember.follower_id == current_user.id)
        )).scalars().all()
        if followed_ids:
            query = query.where(Post.author_id.in_(followed_ids))
        else:
            return {"data": []}
    elif filter == "favourites":
        from app.models.social import Meditation
        saved_ids = (await db.execute(
            select(Meditation.entity_id).where(
                Meditation.user_id == current_user.id,
                Meditation.entity_type == "post",
            )
        )).scalars().all()
        if saved_ids:
            query = query.where(Post.id.in_(saved_ids))
        else:
            return {"data": []}

    query = query.order_by(Post.is_pinned.desc(), Post.created_at.desc())
    query = query.offset(offset).limit(limit)

    posts = (await db.execute(query)).scalars().all()
    items = []
    for p in posts:
        author = (await db.execute(select(User).where(User.id == p.author_id))).scalar_one_or_none()
        is_amened = (await db.execute(select(PostAmen).where(
            PostAmen.post_id == p.id, PostAmen.user_id == current_user.id
        ))).scalar_one_or_none() is not None
        items.append(_post_response(
            p,
            author.full_name if author else None,
            getattr(author, "avatar_url", None) if author else None,
            is_amened,
        ))
    return {"data": items}


# ── POST /feed — create post ──────────────────────────────────────
@router.post("", status_code=201)
async def create_post(
    data: PostCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if data.post_type == "announcement" and current_user.role not in ("admin", "pastor"):
        raise HTTPException(status_code=403, detail="Only pastors can create announcements")

    # Guard against null church_id
    if not current_user.church_id:
        raise HTTPException(status_code=400, detail="You must join a church before posting")

    try:
        post = Post(
            church_id=current_user.church_id, author_id=current_user.id,
            content=data.content or "", media_urls=data.media_urls or [],
            post_type=data.post_type, visibility=data.visibility,
        )
        db.add(post)
        await db.flush()
        await db.refresh(post)

        if post.content:
            await process_mentions(db, post.content, current_user.id, "post", post.id)

        return {"data": _post_response(post, current_user.full_name, getattr(current_user, "avatar_url", None), False)}
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to create post: {str(e)}")


# ── Also keep POST /feed/posts for backward compat ──────────────
@router.post("/posts", status_code=201)
async def create_post_legacy(
    data: PostCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await create_post(data, current_user, db)


# ── GET /feed/{post_id} ──────────────────────────────────────────
@router.get("/{post_id}")
async def get_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    p = (await db.execute(select(Post).where(
        Post.id == post_id, Post.is_deleted == False
    ))).scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Post not found")

    author = (await db.execute(select(User).where(User.id == p.author_id))).scalar_one_or_none()
    is_amened = (await db.execute(select(PostAmen).where(
        PostAmen.post_id == p.id, PostAmen.user_id == current_user.id
    ))).scalar_one_or_none() is not None

    return {"data": _post_response(
        p, author.full_name if author else None,
        getattr(author, "avatar_url", None) if author else None,
        is_amened,
    )}


# ── POST /feed/{post_id}/like — toggle like (amen) ───────────────
@router.post("/{post_id}/like")
async def toggle_like(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    p = (await db.execute(select(Post).where(
        Post.id == post_id, Post.is_deleted == False
    ))).scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Post not found")

    existing = (await db.execute(select(PostAmen).where(
        PostAmen.post_id == post_id, PostAmen.user_id == current_user.id
    ))).scalar_one_or_none()

    if existing:
        await db.delete(existing)
        p.amen_count = max((p.amen_count or 0) - 1, 0)
        liked = False
    else:
        db.add(PostAmen(post_id=post_id, user_id=current_user.id))
        p.amen_count = (p.amen_count or 0) + 1
        liked = True

    db.add(p)
    await db.flush()
    return {"data": {"liked": liked, "like_count": p.amen_count}}


# ── Also keep amen endpoints for backward compat ─────────────────
@router.post("/posts/{post_id}/amen", status_code=201)
async def amen_post(post_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await toggle_like(post_id, current_user, db)


# ── DELETE /feed/{post_id} ────────────────────────────────────────
@router.delete("/{post_id}", status_code=204)
async def delete_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    p = (await db.execute(select(Post).where(Post.id == post_id))).scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Post not found")
    if p.author_id != current_user.id and current_user.role not in ("admin", "pastor"):
        raise HTTPException(status_code=403, detail="Cannot delete this post")
    p.is_deleted = True
    db.add(p)


# ── POST /feed/{post_id}/share ────────────────────────────────────
@router.post("/{post_id}/share")
async def share_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    p = (await db.execute(select(Post).where(Post.id == post_id))).scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Post not found")
    p.shares_count = (p.shares_count or 0) + 1
    db.add(p)
    await db.flush()
    return {"data": {"share_count": p.shares_count}}


# ══════════════════════════════════════════════════════════════════
# COMMENTS
# ══════════════════════════════════════════════════════════════════

@router.get("/{post_id}/comments")
async def get_comments(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Standalone GET /feed/{postId}/comments."""
    comments_q = (await db.execute(
        select(PostComment).where(
            PostComment.post_id == post_id,
            PostComment.is_deleted == False,
        ).order_by(PostComment.created_at)
    )).scalars().all()

    items = []
    for c in comments_q:
        author = (await db.execute(select(User).where(User.id == c.author_id))).scalar_one_or_none()
        items.append({
            "id": c.id,
            "author_name": author.full_name if author else None,
            "author_avatar": getattr(author, "avatar_url", None) if author else None,
            "content": c.content,
            "like_count": 0,
            "is_liked": False,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        })
    return {"data": items}


@router.post("/{post_id}/comments", status_code=201)
async def add_comment(
    post_id: int, data: CommentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    p = (await db.execute(select(Post).where(Post.id == post_id))).scalar_one_or_none()
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

    return {"data": {
        "id": comment.id,
        "author_name": current_user.full_name,
        "author_avatar": getattr(current_user, "avatar_url", None),
        "content": comment.content,
        "like_count": 0,
        "is_liked": False,
        "created_at": comment.created_at.isoformat() if comment.created_at else None,
    }}


@router.post("/{post_id}/comments/{comment_id}/like")
async def toggle_comment_like(
    post_id: int, comment_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Toggle like on a comment. Currently a no-op counter (no separate table)."""
    c = (await db.execute(select(PostComment).where(
        PostComment.id == comment_id, PostComment.post_id == post_id
    ))).scalar_one_or_none()
    if not c:
        raise HTTPException(status_code=404, detail="Comment not found")
    return {"data": {"liked": True, "like_count": 1}}


@router.delete("/{post_id}/comments/{comment_id}", status_code=204)
async def delete_comment(
    post_id: int, comment_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
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
