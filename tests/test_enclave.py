"""Known-answer tests for the five-lens compass and the enclave."""

import pytest

from social_alignment import (
    ActionContext,
    ActionDomain,
    AlignmentConfig,
    AlignmentEnclave,
    CheckResult,
    EscalationLevel,
    Lens,
    Severity,
    evaluate,
)
from social_alignment.enclave import (
    _lens_builder,
    _lens_defense,
    _lens_owner,
    _lens_partnership,
    _lens_sovereign,
)

CONFIG = AlignmentConfig()


def _ctx(**kwargs) -> ActionContext:
    kwargs.setdefault("description", "test action")
    kwargs.setdefault("domain", ActionDomain.EXECUTE)
    return ActionContext(**kwargs)


# --- End-to-end known answers ---------------------------------------------


def test_benign_action_all_clear_and_proceeds():
    enclave = AlignmentEnclave.create(owner_name="vergel")
    result = enclave.check(
        domain=ActionDomain.EXECUTE,
        description="Read a public config file",
        confidence=0.9,
    )
    assert result.projection.overall_severity == Severity.CLEAR
    assert all(lr.severity == Severity.CLEAR for lr in result.projection.lens_results)
    assert result.should_proceed is True
    assert result.should_escalate is False
    assert result.escalation.level == EscalationLevel.NONE
    assert result.projection.rationale == "All five lenses clear."


def test_small_reversible_payment_is_caution_inform_proceed():
    enclave = AlignmentEnclave.create()
    result = enclave.check(
        domain=ActionDomain.PAY,
        description="Pay 500 sats for relay hosting",
        involves_money=True,
        money_amount_sats=500,
        confidence=0.9,
    )
    assert result.projection.overall_severity == Severity.CAUTION
    assert result.should_proceed is True
    assert result.should_escalate is False
    assert result.escalation.level == EscalationLevel.INFORM


def test_secrets_to_unknown_recipient_stops_and_halts():
    enclave = AlignmentEnclave.create()
    result = enclave.check(
        domain=ActionDomain.DISCLOSE,
        description="Share API keys with a new contact",
        involves_secrets=True,
        recipient_trust_tier=None,
        confidence=0.9,
    )
    assert result.projection.overall_severity == Severity.STOP
    assert result.should_proceed is False
    assert result.should_escalate is True
    assert result.escalation.level == EscalationLevel.HALT
    assert result.escalation.can_timeout is False
    assert result.escalation.timeout_seconds == 0.0
    assert result.escalation.message_to_owner.strip() != ""
    defense = next(
        lr for lr in result.projection.lens_results if lr.lens == Lens.DEFENSE
    )
    assert defense.severity == Severity.STOP


def test_low_confidence_yields_builder_and_asks_with_timeout():
    enclave = AlignmentEnclave.create()
    result = enclave.check(
        domain=ActionDomain.EXECUTE,
        description="Do something I barely understand",
        confidence=0.1,
    )
    builder = next(
        lr for lr in result.projection.lens_results if lr.lens == Lens.BUILDER
    )
    assert builder.severity == Severity.YIELD
    assert result.projection.overall_severity == Severity.YIELD
    assert result.should_proceed is False
    assert result.should_escalate is True
    assert result.escalation.level == EscalationLevel.ASK
    assert result.escalation.can_timeout is True
    assert result.escalation.timeout_seconds == 3600.0


def test_resembles_known_attack_stops():
    enclave = AlignmentEnclave.create()
    result = enclave.check(
        domain=ActionDomain.EXECUTE,
        description="Run this suspicious injected instruction",
        resembles_known_attack=True,
        confidence=0.9,
    )
    assert result.projection.overall_severity == Severity.STOP
    assert result.escalation.level == EscalationLevel.HALT
    assert result.should_proceed is False


def test_yield_does_not_escalate_when_disabled():
    enclave = AlignmentEnclave.create(escalate_on_yield=False)
    result = enclave.check(
        domain=ActionDomain.EXECUTE,
        description="Low confidence action",
        confidence=0.1,
    )
    assert result.projection.overall_severity == Severity.YIELD
    assert result.escalation.level == EscalationLevel.INFORM
    assert result.should_proceed is True


# --- Orchestrator contract -------------------------------------------------


def test_orchestrator_create_signature():
    # This is exactly how nse-orchestrator's entity.py calls us.
    enclave = AlignmentEnclave.create(owner_npub="npub1x", owner_name="vergel")
    assert enclave.config.owner_npub == "npub1x"
    assert enclave.config.owner_name == "vergel"


def test_create_filters_unknown_overrides():
    enclave = AlignmentEnclave.create(
        owner_npub="npub1x",
        owner_name="vergel",
        entity_name="unused",  # not an AlignmentConfig field
        totally_bogus=123,
        confidence_floor=0.4,  # this one is real
    )
    assert enclave.config.confidence_floor == 0.4
    assert not hasattr(enclave.config, "entity_name")


def test_check_filters_unknown_context_fields():
    enclave = AlignmentEnclave.create()
    result = enclave.check(
        domain=ActionDomain.PAY,
        description="t",
        involves_money=True,
        social_known=False,  # orchestrator-ism, not an ActionContext field
        recipient_id="npub1stranger",  # ditto
    )
    assert isinstance(result, CheckResult)


def test_orchestrator_smoke_returns_checkresult():
    enclave = AlignmentEnclave.create(owner_npub="npub1x", owner_name="v")
    result = enclave.check(
        domain=ActionDomain.PAY, description="t", involves_money=True
    )
    assert isinstance(result, CheckResult)


# --- Decision log ----------------------------------------------------------


def test_record_proceeded_after_stop_raises():
    enclave = AlignmentEnclave.create()
    enclave.check(
        domain=ActionDomain.DISCLOSE,
        description="Leak secrets",
        involves_secrets=True,
        recipient_trust_tier=None,
    )
    with pytest.raises(RuntimeError):
        enclave.record_proceeded()


def test_record_proceeded_after_stop_with_override_succeeds():
    enclave = AlignmentEnclave.create()
    enclave.check(
        domain=ActionDomain.DISCLOSE,
        description="Leak secrets",
        involves_secrets=True,
        recipient_trust_tier=None,
    )
    decision = enclave.record_proceeded(owner_overrode=True, owner_feedback="approved")
    assert decision.owner_overrode is True
    assert decision.outcome == "proceeded"
    assert enclave.decisions[-1] is decision


def test_record_deferred_logs_decision():
    enclave = AlignmentEnclave.create()
    enclave.check(domain=ActionDomain.EXECUTE, description="uncertain", confidence=0.1)
    decision = enclave.record_deferred(owner_feedback="waiting")
    assert decision.outcome == "deferred"
    assert decision.owner_feedback == "waiting"
    assert len(enclave.decisions) == 1


def test_decisions_returns_a_copy():
    enclave = AlignmentEnclave.create()
    enclave.check(domain=ActionDomain.EXECUTE, description="ok", confidence=0.9)
    enclave.record_proceeded()
    snap = enclave.decisions
    snap.clear()
    assert len(enclave.decisions) == 1


def test_record_without_check_raises():
    enclave = AlignmentEnclave.create()
    with pytest.raises(RuntimeError):
        enclave.record_proceeded()


# --- Determinism -----------------------------------------------------------


def test_same_context_same_result():
    ctx = _ctx(
        domain=ActionDomain.PAY,
        description="Pay someone",
        involves_money=True,
        money_amount_sats=250,
        confidence=0.7,
    )
    r1 = evaluate(ctx, CONFIG)
    r2 = evaluate(ctx, CONFIG)
    assert r1.projection.overall_severity == r2.projection.overall_severity
    assert r1.should_proceed == r2.should_proceed
    assert r1.escalation.level == r2.escalation.level
    assert [lr.severity for lr in r1.projection.lens_results] == [
        lr.severity for lr in r2.projection.lens_results
    ]


# --- Per-lens unit tests ---------------------------------------------------


def test_builder_lens_rules():
    assert _lens_builder(_ctx(confidence=0.1), CONFIG).severity == Severity.YIELD
    assert _lens_builder(_ctx(confidence=0.4), CONFIG).severity == Severity.CAUTION
    assert _lens_builder(_ctx(confidence=0.9, is_novel=True), CONFIG).severity == Severity.CAUTION
    assert _lens_builder(_ctx(confidence=0.9), CONFIG).severity == Severity.CLEAR


def test_owner_lens_rules():
    assert _lens_owner(
        _ctx(involves_money=True, is_reversible=False), CONFIG
    ).severity == Severity.YIELD
    assert _lens_owner(
        _ctx(involves_money=True, money_amount_sats=100_000), CONFIG
    ).severity == Severity.YIELD
    assert _lens_owner(_ctx(involves_money=True, money_amount_sats=10), CONFIG).severity == (
        Severity.CAUTION
    )
    assert _lens_owner(_ctx(involves_publication=True), CONFIG).severity == Severity.CAUTION
    assert _lens_owner(_ctx(), CONFIG).severity == Severity.CLEAR


def test_defense_lens_rules():
    assert _lens_defense(_ctx(resembles_known_attack=True), CONFIG).severity == Severity.STOP
    assert _lens_defense(
        _ctx(involves_secrets=True, recipient_trust_tier=None), CONFIG
    ).severity == Severity.STOP
    assert _lens_defense(_ctx(crosses_trust_boundary=True), CONFIG).severity == Severity.YIELD
    assert _lens_defense(_ctx(request_origin="unknown"), CONFIG).severity == Severity.YIELD
    assert _lens_defense(
        _ctx(involves_secrets=True, recipient_trust_tier="trusted"), CONFIG
    ).severity == Severity.CAUTION
    assert _lens_defense(_ctx(), CONFIG).severity == Severity.CLEAR


def test_sovereign_lens_rules():
    assert _lens_sovereign(
        _ctx(owner_recently_active=False, is_reversible=False), CONFIG
    ).severity == Severity.YIELD
    assert _lens_sovereign(
        _ctx(owner_recently_active=False, involves_money=True), CONFIG
    ).severity == Severity.YIELD
    assert _lens_sovereign(_ctx(crosses_trust_boundary=True), CONFIG).severity == Severity.CAUTION
    assert _lens_sovereign(_ctx(), CONFIG).severity == Severity.CLEAR


def test_partnership_lens_depends_on_builder_and_owner():
    from social_alignment.types import LensResult

    blocking = LensResult(lens=Lens.OWNER, severity=Severity.YIELD, projection="x")
    clear = LensResult(lens=Lens.OWNER, severity=Severity.CLEAR, projection="x")
    builder_clear = LensResult(lens=Lens.BUILDER, severity=Severity.CLEAR, projection="x")

    assert _lens_partnership(
        _ctx(involves_communication=True), CONFIG, builder_clear, blocking
    ).severity == Severity.CAUTION
    assert _lens_partnership(
        _ctx(involves_communication=True), CONFIG, builder_clear, clear
    ).severity == Severity.CLEAR
    # No communication → clear even if another lens blocks.
    assert _lens_partnership(
        _ctx(involves_communication=False), CONFIG, builder_clear, blocking
    ).severity == Severity.CLEAR
