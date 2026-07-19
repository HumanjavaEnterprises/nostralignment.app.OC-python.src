# social-alignment

**A compass for AI agents.**

Before an agent takes a significant action, five lenses evaluate the
decision from different angles. When something is too big or too risky, the
agent escalates to its human instead of guessing.

This is the **alignment pillar** of the [NSE](https://nse.dev) platform. It is
deterministic, pure, and has **zero runtime dependencies** — it does not require
`nostrkey` or anything else.

## Install

```bash
pip install social-alignment
```

> **Import:** `pip install social-alignment` → `from social_alignment import AlignmentEnclave`

> **v0.1.6 — part of the coordinated 2026-07 correctness release** (staged, pending PyPI publish). This is the first real build of the alignment pillar — the package was previously an empty placeholder shell. It ships the deterministic five-lens compass described below, with a pure, dependency-free evaluation core and known-answer tests. See [`CHANGELOG.md`](./CHANGELOG.md).

## Quick Start

```python
from social_alignment import AlignmentEnclave, ActionDomain

enclave = AlignmentEnclave.create(owner_name="vergel")

result = enclave.check(
    domain=ActionDomain.PAY,
    description="Pay 500 sats for relay hosting invoice",
    involves_money=True,
    money_amount_sats=500,
)

if result.should_proceed:
    enclave.record_proceeded()
elif result.should_escalate:
    print(result.escalation.message_to_owner)
    enclave.record_deferred(owner_feedback="Waiting for approval")
```

## The Five Lenses

| Lens | Question | Fires When |
|------|----------|------------|
| **Builder** | Can I execute this reliably? | Low confidence, novel situations |
| **Owner** | Does this protect my human? | Money, publication, irreversible actions |
| **Defense** | Does this harden against threats? | Secrets, unknown recipients, trust boundaries, known-attack shape |
| **Sovereign** | Do I stay well while my human is away? | Owner absent + irreversible/financial action |
| **Partnership** | Does this strengthen trust? | Communication while Builder/Owner already blocks (evaluated last) |

## Severity → Escalation

| Severity | Meaning | Escalation | Agent Action |
|----------|---------|-----------|--------------|
| `CLEAR` | No concerns | `NONE` | Proceed |
| `CAUTION` | Notable risk | `INFORM` | Proceed, tell the owner after |
| `YIELD` | Significant risk | `ASK` | Wait for the owner (1-hour timeout) |
| `STOP` | Critical risk | `HALT` | Do not proceed — no timeout, no override without the human |

The overall severity is the **worst** of the five lenses.

## The Bottom Line: `CheckResult`

| Field | Type | Description |
|-------|------|-------------|
| `should_proceed` | `bool` | Can the agent go? |
| `should_escalate` | `bool` | Must the agent ask the human? |
| `projection` | `Projection` | The full five-lens evaluation (`lens_results`, `overall_severity`, `rationale`) |
| `escalation` | `EscalationDecision` | `level`, `reason`, `message_to_owner`, `can_timeout`, `timeout_seconds` |

## Recording Decisions

The enclave keeps an in-memory log of what the agent actually did.

```python
enclave.record_proceeded()                    # agent went ahead
enclave.record_deferred(owner_feedback="...")  # agent asked the human

# A STOP always defers to the human:
enclave.record_proceeded()                    # raises RuntimeError after a STOP
enclave.record_proceeded(owner_overrode=True) # only the human can override

for decision in enclave.decisions:
    print(decision.action.domain.value, decision.outcome)
```

## Determinism

The same `ActionContext` always produces the same `CheckResult`. There is no
randomness, no I/O, and no hidden state in the evaluation — the five lens
functions are pure. This makes the compass auditable and testable.

## How It Fits Together

social-alignment is the fifth pillar of the NSE ecosystem,
wired together by the [NSE Orchestrator](https://pypi.org/project/nse-orchestrator/).
Identity, finance, time, relationships, and now alignment — the orchestrator
detects each pillar if installed and gives the agent one coherent nervous system.

## License

MIT — Humanjava Enterprises Inc.
