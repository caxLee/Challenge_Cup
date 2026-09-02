"""Framework adapters."""

from .approval import ApprovalResult, FidesApprovalAdapter
from .fides import FidesLabelAdapter, FidesRuntimeAdapter

__all__ = [
    "ApprovalResult",
    "FidesApprovalAdapter",
    "FidesLabelAdapter",
    "FidesRuntimeAdapter",
]
