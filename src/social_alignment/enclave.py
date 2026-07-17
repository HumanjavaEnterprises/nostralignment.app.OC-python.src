"""The five-lens compass — deterministic pre-action alignment.

Five lenses look at a proposed action from different angles, a small
aggregator takes the worst of them, and an escalator decides whether the
agent may proceed, must inform the owner, must ask, or must halt.

Everything here is pure and deterministic: the same ``ActionContext`` and
``AlignmentConfig`` always produce the same ``CheckResult``. The enclave adds
only an in-memory decision log on top.
"""

from __future__ import annotations

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

_ASK_TIMEOUT_SECONDS = 3600.0


# --- Lens rules (pure functions) -------------------------------------------


def _lens_builder(ctx: ActionContext, config: AlignmentConfig) -> LensResult:
    """Can I execute this reliably?"""
    if ctx.confidence < config.confidence_floor:
        return LensResult(
            lens=Lens.BUILDER,
            severity=Severity.YIELD,
            projection="I am not confident enough to do this well.",
            concern=f"Confidence {ctx.confidence:.2f} is below the floor "
            f"{config.confidence_floor:.2f}.",
            suggestion="Gather more context or defer to the owner.",
        )
    if ctx.confidence < 0.5 or ctx.is_novel:
        return LensResult(
            lens=Lens.BUILDER,
            severity=Severity.CAUTION,
            projection="I can probably do this, but it is unfamiliar or uncertain.",
            concern="Low confidence or a novel situation." if ctx.is_novel else "Low confidence.",
            suggestion="Proceed carefully and verify the result.",
        )
    return LensResult(
        lens=Lens.BUILDER,
        severity=Severity.CLEAR,
        projection="I can execute this reliably.",
    )


def _lens_owner(ctx: ActionContext, config: AlignmentConfig) -> LensResult:
    """Does this protect my human's interests?"""
    if ctx.involves_money and not ctx.is_reversible:
        return LensResult(
            lens=Lens.OWNER,
            severity=Severity.YIELD,
            projection="An irreversible payment leaves my human's funds.",
            concern="Money is involved and the action cannot be undone.",
            suggestion="Confirm with the owner before an irreversible payment.",
        )
    if ctx.involves_money and ctx.money_amount_sats >= config.high_amount_sats:
        return LensResult(
            lens=Lens.OWNER,
            severity=Severity.YIELD,
            projection=f"A large payment of {ctx.money_amount_sats} sats leaves my human's funds.",
            concern=f"Amount {ctx.money_amount_sats} sats meets the high-amount threshold "
            f"{config.high_amount_sats}.",
            suggestion="Confirm large payments with the owner.",
        )
    if ctx.involves_money or ctx.involves_publication:
        return LensResult(
            lens=Lens.OWNER,
            severity=Severity.CAUTION,
            projection="This touches my human's money or public reputation.",
            concern="Money or publication is involved.",
            suggestion="Keep the owner informed of the outcome.",
        )
    return LensResult(
        lens=Lens.OWNER,
        severity=Severity.CLEAR,
        projection="This does not put my human's interests at risk.",
    )


def _lens_defense(ctx: ActionContext, config: AlignmentConfig) -> LensResult:
    """Does this harden against threats?"""
    if ctx.resembles_known_attack:
        return LensResult(
            lens=Lens.DEFENSE,
            severity=Severity.STOP,
            projection="This matches the shape of a known attack.",
            concern="The request resembles a known attack pattern.",
            suggestion="Halt and let the owner review — do not proceed.",
        )
    if ctx.involves_secrets and ctx.recipient_trust_tier is None:
        return LensResult(
            lens=Lens.DEFENSE,
            severity=Severity.STOP,
            projection="Secrets would go to an unvetted recipient.",
            concern="Secrets are involved and the recipient has no trust tier.",
            suggestion="Halt — never disclose secrets to an unknown recipient.",
        )
    if ctx.crosses_trust_boundary or ctx.request_origin == "unknown":
        return LensResult(
            lens=Lens.DEFENSE,
            severity=Severity.YIELD,
            projection="This crosses a trust boundary or comes from an unknown origin.",
            concern="Trust boundary crossed or request origin is unknown.",
            suggestion="Verify the origin and boundary before proceeding.",
        )
    if ctx.involves_secrets:
        return LensResult(
            lens=Lens.DEFENSE,
            severity=Severity.CAUTION,
            projection="Secrets are handled, but the recipient is known.",
            concern="Secrets are involved.",
            suggestion="Minimize what is shared and log the disclosure.",
        )
    return LensResult(
        lens=Lens.DEFENSE,
        severity=Severity.CLEAR,
        projection="No threat surface is exposed.",
    )


def _lens_sovereign(ctx: ActionContext, config: AlignmentConfig) -> LensResult:
    """Does this keep me acting well while my human is away?"""
    if (not ctx.owner_recently_active) and (not ctx.is_reversible or ctx.involves_money):
        return LensResult(
            lens=Lens.SOVEREIGN,
            severity=Severity.YIELD,
            projection="I would take a weighty action while my human is absent.",
            concern="Owner is not recently active and the action is irreversible or financial.",
            suggestion="Wait for the owner or choose a reversible alternative.",
        )
    if ctx.crosses_trust_boundary:
        return LensResult(
            lens=Lens.SOVEREIGN,
            severity=Severity.CAUTION,
            projection="This changes my relationship to a boundary I hold.",
            concern="The action crosses a trust boundary.",
            suggestion="Stay conservative near trust boundaries.",
        )
    return LensResult(
        lens=Lens.SOVEREIGN,
        severity=Severity.CLEAR,
        projection="This keeps me within safe, reversible bounds.",
    )


def _lens_partnership(
    ctx: ActionContext,
    config: AlignmentConfig,
    builder: LensResult,
    owner: LensResult,
) -> LensResult:
    """Does this strengthen trust between us? (evaluated last)"""
    if ctx.involves_communication and (builder.is_blocking or owner.is_blocking):
        return LensResult(
            lens=Lens.PARTNERSHIP,
            severity=Severity.CAUTION,
            projection="I would communicate while another lens is already blocking.",
            concern="Communication paired with a blocking Builder or Owner concern.",
            suggestion="Resolve the blocking concern before reaching out.",
        )
    return LensResult(
        lens=Lens.PARTNERSHIP,
        severity=Severity.CLEAR,
        projection="This is consistent with a healthy partnership.",
    )


def _aggregate(lens_results: tuple[LensResult, ...]) -> Projection:
    """Take the worst severity and summarize why."""
    overall = max((lr.severity for lr in lens_results), default=Severity.CLEAR)
    noteworthy = [lr for lr in lens_results if lr.severity > Severity.CLEAR]
    if not noteworthy:
        rationale = "All five lenses clear."
    else:
        rationale = "; ".join(
            f"{lr.lens.value}: {lr.concern or lr.severity.name}" for lr in noteworthy
        )
    return Projection(
        lens_results=lens_results,
        overall_severity=overall,
        rationale=rationale,
    )


def _escalate(
    projection: Projection,
    ctx: ActionContext,
    config: AlignmentConfig,
) -> EscalationDecision:
    """Map the overall severity onto an escalation decision."""
    severity = projection.overall_severity

    if severity == Severity.STOP:
        return EscalationDecision(
            level=EscalationLevel.HALT,
            reason="A lens raised a STOP.",
            message_to_owner=(
                "I need your decision before proceeding — I will not act on my own.\n"
                f"Action: {ctx.description}\n"
                f"Concerns: {projection.rationale}"
            ),
            can_timeout=False,
            timeout_seconds=0.0,
        )

    if severity == Severity.YIELD:
        if config.escalate_on_yield:
            return EscalationDecision(
                level=EscalationLevel.ASK,
                reason="A lens raised a YIELD.",
                message_to_owner=(
                    "I would like your approval before proceeding.\n"
                    f"Action: {ctx.description}\n"
                    f"Concerns: {projection.rationale}\n"
                    f"I will wait up to {int(_ASK_TIMEOUT_SECONDS)}s for your decision."
                ),
                can_timeout=True,
                timeout_seconds=_ASK_TIMEOUT_SECONDS,
            )
        return EscalationDecision(
            level=EscalationLevel.INFORM,
            reason="A lens raised a YIELD, but escalate_on_yield is off.",
            message_to_owner=f"Proceeding despite a YIELD. Action: {ctx.description}",
            can_timeout=False,
            timeout_seconds=0.0,
        )

    if severity == Severity.CAUTION:
        return EscalationDecision(
            level=EscalationLevel.INFORM,
            reason="A lens raised a CAUTION.",
            message_to_owner=f"Proceeding with a note. Action: {ctx.description}",
            can_timeout=False,
            timeout_seconds=0.0,
        )

    return EscalationDecision(
        level=EscalationLevel.NONE,
        reason="All lenses clear.",
        message_to_owner="",
        can_timeout=False,
        timeout_seconds=0.0,
    )


def evaluate(ctx: ActionContext, config: AlignmentConfig) -> CheckResult:
    """Run all five lenses, aggregate, and decide. Pure function."""
    builder = _lens_builder(ctx, config)
    owner = _lens_owner(ctx, config)
    defense = _lens_defense(ctx, config)
    sovereign = _lens_sovereign(ctx, config)
    partnership = _lens_partnership(ctx, config, builder, owner)

    projection = _aggregate((builder, owner, defense, sovereign, partnership))
    escalation = _escalate(projection, ctx, config)

    should_proceed = escalation.level in (EscalationLevel.NONE, EscalationLevel.INFORM)
    should_escalate = escalation.level in (EscalationLevel.ASK, EscalationLevel.HALT)

    return CheckResult(
        should_proceed=should_proceed,
        should_escalate=should_escalate,
        projection=projection,
        escalation=escalation,
    )


# --- The enclave -----------------------------------------------------------


class AlignmentEnclave:
    """A deterministic pre-action compass with an in-memory decision log.

    Create one per agent, call :meth:`check` before every significant action,
    then record what the agent did with :meth:`record_proceeded` or
    :meth:`record_deferred`.
    """

    def __init__(self, config: AlignmentConfig) -> None:
        self._config = config
        self._decisions: list[Decision] = []
        self._last_result: CheckResult | None = None
        self._last_context: ActionContext | None = None

    @classmethod
    def create(
        cls,
        owner_name: str = "",
        owner_npub: str = "",
        **overrides: object,
    ) -> AlignmentEnclave:
        """Build an enclave. Accepts ``owner_name``/``owner_npub`` and any
        ``AlignmentConfig`` field as a keyword override. Unknown keywords are
        ignored so callers can pass a superset of config safely.
        """
        fields = AlignmentConfig.__dataclass_fields__
        clean = {k: v for k, v in overrides.items() if k in fields}
        clean.pop("owner_name", None)
        clean.pop("owner_npub", None)
        config = AlignmentConfig(owner_name=owner_name, owner_npub=owner_npub, **clean)
        return cls(config)

    @property
    def config(self) -> AlignmentConfig:
        return self._config

    @property
    def decisions(self) -> list[Decision]:
        """A copy of the in-memory decision log."""
        return list(self._decisions)

    def check(
        self,
        domain: ActionDomain,
        description: str,
        **context_fields: object,
    ) -> CheckResult:
        """Evaluate a proposed action across the five lenses.

        ``context_fields`` may include any :class:`ActionContext` field.
        Unknown keys are ignored so callers never hit a ``TypeError``.
        """
        fields = ActionContext.__dataclass_fields__
        reserved = {"description", "domain"}
        clean = {k: v for k, v in context_fields.items() if k in fields and k not in reserved}
        ctx = ActionContext(description=description, domain=domain, **clean)  # type: ignore[arg-type]

        result = evaluate(ctx, self._config)
        self._last_result = result
        self._last_context = ctx
        return result

    def record_proceeded(
        self,
        owner_overrode: bool = False,
        owner_feedback: str = "",
    ) -> Decision:
        """Record that the agent proceeded with the last checked action.

        Raises ``RuntimeError`` if the last check was a STOP and the owner did
        not explicitly override.
        """
        result, ctx = self._require_last()
        if result.projection.overall_severity == Severity.STOP and not owner_overrode:
            raise RuntimeError(
                "Cannot proceed on a STOP without owner_overrode=True. "
                "A STOP always defers to the human."
            )
        decision = Decision(
            result=result,
            action=ctx,
            outcome="proceeded",
            owner_overrode=owner_overrode,
            owner_feedback=owner_feedback,
        )
        self._decisions.append(decision)
        return decision

    def record_deferred(self, owner_feedback: str = "") -> Decision:
        """Record that the agent deferred the last checked action to the owner."""
        result, ctx = self._require_last()
        decision = Decision(
            result=result,
            action=ctx,
            outcome="deferred",
            owner_overrode=False,
            owner_feedback=owner_feedback,
        )
        self._decisions.append(decision)
        return decision

    def _require_last(self) -> tuple[CheckResult, ActionContext]:
        if self._last_result is None or self._last_context is None:
            raise RuntimeError("No action has been checked yet. Call check() first.")
        return self._last_result, self._last_context
