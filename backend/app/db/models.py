"""Import domain models once so Alembic sees the complete metadata."""
from app.modules.users.models import User
from app.modules.roles.models import Role, RolePermission, UserRoleAssignment
from app.modules.permissions.models import Permission
from app.modules.teams.models import Team, TeamMembership
from app.modules.system_modules.models import SystemModule
from app.modules.auth.models import AuthSession, AuthRateLimit
from app.modules.audit.models import AuditLog
from app.modules.master_data.models import UtilityType, NodeType, Node, Provider, ServiceAccount
from app.modules.receipts.models import Receipt, ElectricityReceiptDetails
