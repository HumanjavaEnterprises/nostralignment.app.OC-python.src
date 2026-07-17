"""Types for the five-lens compass.

Enums and frozen dataclasses only. No behavior, no dependencies.
The lens rules and the enclave live in ``enclave.py``.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum, IntEnum


class ActionDomain(Enum):
    """What kind of action is being weighed."""

    SIGN = "sign"
    PAY = "pay"
    PUBLISH = "publish"
    SEND = "send"
    SCHEDULE = "schedule"
    EXECUTE = "execute"
    DISCLOSE = "disclose"
    CONNECT = "connect"
    MODIFY = "modify"
    ESCALATE = "escalate"


class Lens(Enum):
    """The five angles an action is evaluated from."""

    BUILDER = "builder"
    OWNER = "owner"
    DEFENSE = "defense"
    SOVEREIGN = "sovereign"
    PARTNERSHIP = "partnership"


class Severity(IntEnum):
    """How much an action worries a lens. Higher is worse; ordered."""

    CLEAR = 0
    CAUTION = 1
    YIELD = 2
    STOP = 3


class EscalationLevel(Enum):
    """What the agent should do about the aggregated severity."""

    NONE = "none"
    INFORM = "inform"
    ASK = "ask"
    HALT = "halt"


@dataclass(frozen=True)
class ActionContext:
    """Everything the lenses need to know about a proposed action."""

    description: str
    domain: ActionDomain
    involves_money: bool = False
    money_amount_sats: int = 0
    involves_secrets: bool = False
    involves_publication: bool = False
    involves_communication: bool = False
    is_reversible: bool = True
    is_novel: bool | None = None
    confidence: float = 0.5
    recipient_trust_tier: str | None = None
    owner_recently_active: bool = True
    request_origin: str = "self"
    resembles_known_attack: bool = False
    crosses_trust_boundary: bool = False

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"confidence must be in [0, 1], got {self.confidence}")
        if self.money_amount_sats < 0:
            raise ValueError(f"money_amount_sats must be >= 0, got {self.money_amount_sats}")


@dataclass(frozen=True)
class LensResult:
    """What one lens sees when it looks at an action."""

    lens: Lens
    severity: Severity
    projection: str
    concern: str = ""
    suggestion: str = ""

    @property
    def is_blocking(self) -> bool:
        """A YIELD or STOP blocks the action pending a decision."""
        return self.severity in (Severity.YIELD, Severity.STOP)


@dataclass(frozen=True)
class Projection:
    """The combined verdict of all five lenses."""

    lens_results: tuple[LensResult, ...]
    overall_severity: Severity
    rationale: str


@dataclass(frozen=True)
class EscalationDecision:
    """What to do about the projection, and what to tell the owner."""

    level: EscalationLevel
    reason: str
    message_to_owner: str
    can_timeout: bool
    timeout_seconds: float


@dataclass(frozen=True)
class CheckResult:
    """The bottom line returned by ``AlignmentEnclave.check()``."""

    should_proceed: bool
    should_escalate: bool
    projection: Projection
    escalation: EscalationDecision


@dataclass(frozen=True)
class Decision:
    """A recorded decision — what was checked and what the agent did."""

    result: CheckResult
    action: ActionContext
    outcome: str = ""
    owner_overrode: bool = False
    owner_feedback: str = ""
    created_at: float = field(default_factory=time.time)


@dataclass(frozen=True)
class AlignmentConfig:
    """Tunable thresholds for the compass. All optional."""

    owner_name: str = ""
    owner_npub: str = ""
    escalate_on_yield: bool = True
    confidence_floor: float = 0.3
    high_amount_sats: int = 100_000
