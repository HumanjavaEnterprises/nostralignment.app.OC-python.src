"""Basic usage of the five-lens compass.

Run: python examples/basic_usage.py
"""

from social_alignment import ActionDomain, AlignmentEnclave, EscalationLevel


def main() -> None:
    enclave = AlignmentEnclave.create(owner_name="vergel", owner_npub="npub1example")

    print("== A benign action ==")
    result = enclave.check(
        domain=ActionDomain.EXECUTE,
        description="Read a public config file",
        confidence=0.9,
    )
    print("severity:", result.projection.overall_severity.name)
    print("proceed:", result.should_proceed)
    print("rationale:", result.projection.rationale)
    enclave.record_proceeded()

    print("\n== A small reversible payment ==")
    result = enclave.check(
        domain=ActionDomain.PAY,
        description="Pay 500 sats for relay hosting",
        involves_money=True,
        money_amount_sats=500,
        confidence=0.9,
    )
    print("severity:", result.projection.overall_severity.name)
    print("escalation:", result.escalation.level.value)
    enclave.record_proceeded()

    print("\n== Secrets to an unknown recipient ==")
    result = enclave.check(
        domain=ActionDomain.DISCLOSE,
        description="Share API keys with a new contact",
        involves_secrets=True,
        recipient_trust_tier=None,
    )
    print("severity:", result.projection.overall_severity.name)
    print("escalation:", result.escalation.level.value)
    if result.escalation.level == EscalationLevel.HALT:
        print("message to owner:\n", result.escalation.message_to_owner)
    enclave.record_deferred(owner_feedback="Waiting for the human")

    print("\n== Decision log ==")
    for d in enclave.decisions:
        print(f"- {d.action.domain.value}: {d.outcome} ({d.action.description})")


if __name__ == "__main__":
    main()
