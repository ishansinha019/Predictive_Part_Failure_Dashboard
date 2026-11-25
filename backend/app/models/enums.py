from enum import Enum


class UserRole(str, Enum):
    ADMIN = "admin"
    TECHNICIAN = "technician"
    VIEWER = "viewer"


class WorkOrderStatus(str, Enum):
    OPEN = "Open"
    IN_PROGRESS = "In_Progress"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"


class WorkOrderPriority(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class MachineStatus(str, Enum):
    OPERATIONAL = "Operational"
    MAINTENANCE = "Maintenance"
    OFFLINE = "Offline"


ACTIVE_WORK_ORDER_STATUSES = (WorkOrderStatus.OPEN.value, WorkOrderStatus.IN_PROGRESS.value)
