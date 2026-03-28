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
from app.models.feed import Post, PostAmen, PostComment  # noqa: F401
from app.models.glory_clip import GloryClip, GloryClipAmen, GloryClipComment, GloryClipView  # noqa: F401
from app.models.event import Event, EventRSVP  # noqa: F401
from app.models.prayer import PrayerRequest, PrayerResponseEntry  # noqa: F401
from app.models.alert import Alert  # noqa: F401
from app.models.sermon import Sermon, SermonNote  # noqa: F401
from app.models.scripture import ServiceScripture  # noqa: F401
from app.models.child_checkin import CheckinSession  # noqa: F401
from app.models.volunteer import (  # noqa: F401
    VolunteerRole, VolunteerSchedule, VolunteerAvailability,
    VolunteerApplication, VolunteerHoursLog,
)
from app.models.asset import Asset  # noqa: F401
from app.models.automation import AutomationRule  # noqa: F401
from app.models.campus import Campus  # noqa: F401
from app.models.discipleship import DiscipleshipStep, MemberDiscipleshipProgress  # noqa: F401
from app.models.store import Product  # noqa: F401
from app.models.task import MinistryTask  # noqa: F401
from app.models.care import CareCase, CareNote  # noqa: F401
from app.models.activity_log import MemberActivityLog  # noqa: F401
from app.models.facility import FacilityRoom, RoomBooking  # noqa: F401
