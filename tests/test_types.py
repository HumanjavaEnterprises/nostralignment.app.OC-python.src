"""Unit tests for the types layer — enums, validation, and small properties."""

import pytest

from social_alignment import (
    ActionContext,
    ActionDomain,
    AlignmentConfig,
    EscalationLevel,
    Lens,
    LensResult,
    Severity,
)


def test_severity_is_ordered():
    assert Severity.CLEAR < Severity.CAUTION < Severity.YIELD < Severity.STOP
    assert max(Severity.CLEAR, Severity.STOP, Severity.CAUTION) == Severity.STOP


def test_all_enums_have_expected_members():
    assert {d.name for d in ActionDomain} == {
        "SIGN", "PAY", "PUBLISH", "SEND", "SCHEDULE",
        "EXECUTE", "DISCLOSE", "CONNECT", "MODIFY", "ESCALATE",
    }
    assert {lens.name for lens in Lens} == {
        "BUILDER", "OWNER", "DEFENSE", "SOVEREIGN", "PARTNERSHIP",
    }
    assert {e.name for e in EscalationLevel} == {"NONE", "INFORM", "ASK", "HALT"}


def test_action_context_defaults():
    ctx = ActionContext(description="do a thing", domain=ActionDomain.EXECUTE)
    assert ctx.confidence == 0.5
    assert ctx.is_reversible is True
    assert ctx.request_origin == "self"
    assert ctx.recipient_trust_tier is None
    assert ctx.is_novel is None


def test_action_context_rejects_bad_confidence():
    with pytest.raises(ValueError):
        ActionContext(description="x", domain=ActionDomain.PAY, confidence=1.5)
    with pytest.raises(ValueError):
        ActionContext(description="x", domain=ActionDomain.PAY, confidence=-0.1)


def test_action_context_rejects_negative_sats():
    with pytest.raises(ValueError):
        ActionContext(description="x", domain=ActionDomain.PAY, money_amount_sats=-1)


def test_action_context_is_frozen():
    ctx = ActionContext(description="x", domain=ActionDomain.PAY)
    with pytest.raises(Exception):
        ctx.confidence = 0.9  # type: ignore[misc]


def test_lens_result_is_blocking():
    clear = LensResult(lens=Lens.BUILDER, severity=Severity.CLEAR, projection="ok")
    caution = LensResult(lens=Lens.BUILDER, severity=Severity.CAUTION, projection="ok")
    yield_ = LensResult(lens=Lens.OWNER, severity=Severity.YIELD, projection="hmm")
    stop = LensResult(lens=Lens.DEFENSE, severity=Severity.STOP, projection="no")
    assert clear.is_blocking is False
    assert caution.is_blocking is False
    assert yield_.is_blocking is True
    assert stop.is_blocking is True


def test_alignment_config_defaults():
    config = AlignmentConfig()
    assert config.escalate_on_yield is True
    assert config.confidence_floor == 0.3
    assert config.high_amount_sats == 100_000
