import re
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.models.social import Mention
from app.models.alert import create_alert

async def process_mentions(db: AsyncSession, text: str, author_id: int, entity_type: str, entity_id: int):
    """Parse text for @usernames, resolve users, and create mentions/notifications."""
    if not text:
        return
        
    # Extract @usernames (alphanumeric and underscore)
    usernames = set(re.findall(r'@([a-zA-Z0-9_]+)', text))
    if not usernames:
        return

    # Find users by username
    query = select(User).where(User.username.in_(usernames))
    mentioned_users = (await db.execute(query)).scalars().all()

    for u in mentioned_users:
        # Don't mention oneself
        if u.id == author_id:
            continue
            
        # Create Mention record
        mention = Mention(
            user_id=u.id, 
            author_id=author_id, 
            entity_type=entity_type, 
            entity_id=entity_id
        )
        db.add(mention)
        
        # Fire notification
        author = (await db.execute(select(User).where(User.id == author_id))).scalar_one_or_none()
        author_name = author.username if author else "Someone"
        
        await create_alert(
            db=db,
            user_id=u.id,
            type="mention",
            title=f"{author_name} mentioned you",
            body=f"{author_name} mentioned you in a {entity_type}.",
            data={"link_type": entity_type, "link_id": entity_id}
        )
