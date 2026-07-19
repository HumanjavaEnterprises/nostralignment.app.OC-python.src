"""social-alignment — a deterministic pre-action five-lens compass.

    from social_alignment import AlignmentEnclave, ActionDomain

    enclave = AlignmentEnclave.create(owner_name="vergel")
    result = enclave.check(
        domain=ActionDomain.PAY,
        description="Pay 500 sats for relay hosting",
        involves_money=True,
        money_amount_sats=500,
    )
    if result.should_proceed:
        enclave.record_proceeded()

Zero runtime dependencies. The alignment pillar of the NSE platform.
"""

from .enclave import AlignmentEnclave, evaluate
from .types import (
    ActionContext,
    ActionDomain,
    AlignmentConfig,
    CheckResult,
    Decision,
    EscalationDecision,
    EscalationLevel,
    Lens,
    LensResult,
    Projection,
    Severity,
)

__version__ = "0.1.5"

__all__ = [
    "__version__",
    "AlignmentEnclave",
    "AlignmentConfig",
    "evaluate",
    "ActionContext",
    "ActionDomain",
    "CheckResult",
    "Decision",
    "EscalationDecision",
    "EscalationLevel",
    "Lens",
    "LensResult",
    "Projection",
    "Severity",
]
