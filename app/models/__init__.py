"""Import all models so Base.metadata.create_all() creates every table."""

from app.models.church import Church  # noqa: F401
from app.models.user import User, AuditLog  # noqa: F401
from app.models.member import Member, MemberNote  # noqa: F401
from app.models.family import Family, FamilyRelationship  # noqa: F401
from app.models.fund import Fund, Budget, Expense  # noqa: F401
from app.models.donation import Donation, Pledge  # noqa: F401
from app.models.attendance import Service, AttendanceRecord, GroupAttendance  # noqa: F401
from app.models.group import Group, GroupMembership  # noqa: F401
from app.models.chat import Conversation, ConversationParticipant, Message  # noqa: F401
from app.models.feed import Post, PostLike, PostComment  # noqa: F401
from app.models.short import Short, ShortLike, ShortComment, ShortView  # noqa: F401
from app.models.event import Event, EventRSVP  # noqa: F401
from app.models.prayer import PrayerRequest, PrayerResponseEntry  # noqa: F401
from app.models.notification import Notification  # noqa: F401
from app.models.sermon import Sermon, SermonNote  # noqa: F401
from app.models.scripture import ServiceScripture  # noqa: F401
