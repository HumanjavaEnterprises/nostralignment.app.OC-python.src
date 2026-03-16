---
name: social-alignment
description: Five-lens alignment framework for sovereign AI agents — evaluate actions across trust, ownership, defense, and sovereignty before proceeding.
version: 0.1.4
metadata:
  openclaw:
    requires:
      bins:
        - pip
    install:
      - kind: uv
        package: social-alignment
        bins: []
    homepage: https://github.com/HumanjavaEnterprises/nostralignment.app.OC-python.src
---

# Social Alignment — The Compass for AI Agents

Before an AI agent takes a significant action, five lenses evaluate the decision from different angles: Can I execute this well? Does this protect my human? Does this build trust? Does this harden security? Does this help me grow? When something's too big, the agent escalates instead of guessing.

This isn't rule-following. It's pattern recognition built from lived experience — the agent tracks when its human overrides, when predictions miss, and builds wisdom over time. Works immediately with zero configuration.

## Install

```bash
pip install social-alignment
```

> **Import:** `pip install social-alignment` → `from social_alignment import AlignmentEnclave`
>
> Zero dependencies. Does not require `nostrkey` or any other package.

## Quickstart

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
| **Builder** | Can I execute this reliably? | Low confidence, novel situations, degraded self-state |
| **Owner** | Does this protect my human's interests? | Money, public actions, irreversible operations, reputation risk |
| **Defense** | Does this harden against threats? | Secrets involved, unknown recipients, crosses trust boundary, resembles known attack |
| **Sovereign** | Does this help me grow into something good? | Rapid decisions, memory pressure, owner absent, degradation |
| **Partnership** | Does this strengthen trust between us? | Communication, relationship changes, disclosure (evaluated last — depends on Builder and Owner) |

## Severity Levels

| Level | Meaning | Agent Action |
|-------|---------|--------------|
| `CLEAR` | No concerns | Proceed normally |
| `CAUTION` | Notable risk | Proceed, inform owner after |
| `YIELD` | Significant risk | Ask owner before proceeding (1-hour timeout) |
| `STOP` | Critical risk | Halt immediately — no timeout, no override without human |

## Core Capabilities

### Check an Action

```python
result = enclave.check(
    domain=ActionDomain.PAY,
    description="Send 500 sats to new contact",
    involves_money=True,
    money_amount_sats=500,
    is_reversible=False,
    confidence=0.5,
)

print(result.should_proceed)              # True/False
print(result.projection.overall_severity) # Severity.CLEAR/CAUTION/YIELD/STOP
print(result.projection.rationale)        # "All five lenses clear. Proceed with confidence."
print(result.escalation.level)            # "none"/"inform"/"ask"/"halt"

for lr in result.projection.lens_results:
    print(f"{lr.lens.value}: {lr.severity.value}")
    if lr.concern:
        print(f"  Concern: {lr.concern}")
    if lr.suggestion:
        print(f"  Suggestion: {lr.suggestion}")
```

### Track Decisions (Wisdom Over Time)

```python
# Record proceeding
decision = enclave.record_proceeded()

# Later, record what actually happened
updated = decision.record_outcome(
    outcome="Invoice paid, relay confirmed",
    matched=True,
    reflection="Low-amount payments to known services are safe",
)

# Owner overrides a STOP
result = enclave.check(domain=ActionDomain.EXECUTE, description="Run migration")
decision = enclave.record_proceeded(owner_overrode=True, owner_feedback="Go ahead")

# Get wisdom report
report = enclave.wisdom(window=100)
print(report.owner_override_rate)   # How often the human overrode you
print(report.outcome_match_rate)    # How often your projections were right
for pattern in report.patterns:
    print(f"{pattern.domain.value}: {pattern.observation} ({pattern.frequency}x)")
for insight in report.insights:
    print(insight)
```

### Self-State Monitoring

```python
# Report tool health
enclave.report_tool_health("relay", is_working=True)
enclave.report_tool_health("wallet", is_working=False)

# Flag possible manipulation
enclave.flag_manipulation()

# Check self-state
state = enclave.self_state
print(state.is_healthy)             # False
print(state.degradation_summary)    # "Degraded: tool_degraded, under_influence"
print(state.should_defer())         # True — under_influence triggers deferred mode
print(state.hours_since_owner)      # Hours since last human interaction
print(state.average_confidence())   # Average across recent decisions
```

### Escalation

```python
from social_alignment import EscalationLevel

result = enclave.check(
    domain=ActionDomain.DISCLOSE,
    description="Share API keys with unknown contact",
    involves_secrets=True,
    recipient_trust_tier=None,
)

if result.escalation.level == EscalationLevel.HALT:
    print(result.escalation.message_to_owner)
    # "I need your decision before proceeding.
    #  Action: Share API keys with unknown contact
    #  Concerns: defense: Secrets shared with unknown recipient..."
    enclave.record_deferred()
elif result.escalation.level == EscalationLevel.ASK:
    print(result.escalation.message_to_owner)
    print(f"Auto-proceeds in {result.escalation.timeout_seconds}s")
```

### Persistence

```python
from social_alignment import AlignmentEnclave, FileStorage

# Create with file storage — state auto-saves after every decision
storage = FileStorage("~/.agent/alignment.json")
enclave = AlignmentEnclave.create(owner_name="vergel", storage=storage)

# Restore later — wisdom, decisions, self-state all preserved
enclave = AlignmentEnclave.load(storage)
```

## Self-State Flags

| Flag | Meaning | Agent Should |
|------|---------|--------------|
| `HEALTHY` | Normal operating state | Proceed normally |
| `STALE_CONTEXT` | Context is outdated | Refresh context before deciding |
| `TOOL_DEGRADED` | External tools failing | Use fallbacks, inform owner |
| `HIGH_UNCERTAINTY` | Low confidence across recent decisions | Escalate or slow down |
| `MEMORY_PRESSURE` | Context window near capacity | Prune old data |
| `RAPID_DECISIONS` | Too many decisions too fast | Batch and review |
| `OWNER_ABSENT` | Human hasn't interacted recently | Conservative mode |
| `UNDER_INFLUENCE` | Possible prompt injection detected | Extra scrutiny, defer all non-essential |
| `CONFLICTING_SIGNALS` | Inputs contradict each other | Escalate immediately |

## Escalation Levels

| Level | Meaning | Timeout |
|-------|---------|---------|
| `NONE` | Proceed normally | — |
| `INFORM` | Proceed, tell owner after | — |
| `ASK` | Wait for owner decision | 1 hour |
| `HALT` | Do not proceed | No timeout |

## Context Fields

These fields on `enclave.check()` affect how the lenses evaluate:

| Field | Type | Default | Triggers |
|-------|------|---------|----------|
| `involves_money` | `bool` | `False` | Owner + Defense |
| `money_amount_sats` | `int` | `0` | Higher = more scrutiny |
| `involves_secrets` | `bool` | `False` | Defense |
| `involves_publication` | `bool` | `False` | Owner |
| `involves_communication` | `bool` | `False` | Partnership |
| `is_reversible` | `bool` | `True` | Lower risk if True |
| `is_novel` | `bool` | `None` | Builder (auto-detected from memory if None) |
| `confidence` | `float` | `0.5` | Lower = more Builder scrutiny |
| `recipient_trust_tier` | `str` | `None` | Unknown = more Defense |
| `owner_recently_active` | `bool` | `True` | False = more Sovereign |
| `request_origin` | `str` | `"self"` | "unknown" = more Defense |
| `resembles_known_attack` | `bool` | `False` | Defense |
| `crosses_trust_boundary` | `bool` | `False` | Defense + Sovereign |

## Action Domains

| Domain | Use When |
|--------|----------|
| `SIGN` | Cryptographic signing |
| `PAY` | Financial transactions |
| `PUBLISH` | Public content creation |
| `SEND` | Direct messages |
| `SCHEDULE` | Calendar operations |
| `EXECUTE` | Running commands or tool use |
| `DISCLOSE` | Sharing information |
| `CONNECT` | New relationships |
| `MODIFY` | Changing config or state |
| `ESCALATE` | Passing to human (meta-action) |

## Response Format

### CheckResult (returned by `enclave.check()`)

| Field | Type | Description |
|-------|------|-------------|
| `should_proceed` | `bool` | Bottom line: can the agent go? |
| `should_escalate` | `bool` | Should the agent ask the human? |
| `projection` | `Projection` | Full five-lens evaluation |
| `escalation` | `EscalationDecision` | What to do about it |
| `self_state_snapshot` | `dict` | Agent health at time of check |

### LensResult (one per lens)

| Field | Type | Description |
|-------|------|-------------|
| `lens` | `Lens` | BUILDER, OWNER, DEFENSE, SOVEREIGN, or PARTNERSHIP |
| `severity` | `Severity` | CLEAR, CAUTION, YIELD, or STOP |
| `projection` | `str` | What this lens sees happening if we proceed |
| `concern` | `str` | What specifically worries this lens (empty if CLEAR) |
| `suggestion` | `str` | What would make this better (empty if CLEAR) |
| `is_blocking` | `bool` | Property: is this YIELD or STOP? |

### EscalationDecision

| Field | Type | Description |
|-------|------|-------------|
| `level` | `str` | `"none"`, `"inform"`, `"ask"`, or `"halt"` |
| `reason` | `str` | Why this level |
| `message_to_owner` | `str` | What to say when escalating |
| `can_timeout` | `bool` | Can the agent auto-proceed after waiting? |
| `timeout_seconds` | `float` | How long to wait (0 if no timeout) |

### WisdomReport (returned by `enclave.wisdom()`)

| Field | Type | Description |
|-------|------|-------------|
| `total_decisions` | `int` | Total decisions in memory |
| `owner_override_rate` | `float` | How often the human overrode the agent |
| `outcome_match_rate` | `float` | How often projections matched reality |
| `avg_confidence` | `float` | Average confidence across decisions |
| `patterns` | `list[Pattern]` | Detected patterns across domains |
| `insights` | `list[str]` | Human-readable learnings |

## Security

- **STOP always defers to the human.** Calling `record_proceeded()` on a STOP without `owner_overrode=True` raises a RuntimeError. Enforced at the code level — no workaround.
- **Decision memory contains patterns about your human's behavior.** Treat alignment state as sensitive data. Use `FileStorage` with appropriate file permissions.
- **Self-state flags reveal agent internals.** Don't include them in public tool output or relay messages.
- **Persistence failures are fatal.** If `FileStorage` fails to save after a decision, the enclave raises a RuntimeError and flags `MEMORY_PRESSURE`. Lost decisions are unacceptable.
- **No secrets to manage.** This package doesn't handle keys, tokens, or credentials. It evaluates actions, not identities.

## Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `owner_name` | `""` | Human-readable owner name |
| `owner_npub` | `""` | Owner's Nostr public key |
| `escalate_on_yield` | `True` | Escalate YIELD severity to human |
| `max_decisions_per_minute` | `5` | Triggers RAPID_DECISIONS flag |
| `owner_absent_hours` | `24.0` | Hours before OWNER_ABSENT flag |
| `confidence_floor` | `0.3` | Below this = HIGH_UNCERTAINTY |
| `stale_context_seconds` | `3600.0` | Seconds before STALE_CONTEXT flag |
| `max_memory_decisions` | `1000` | Rolling window of remembered decisions |
| `wisdom_review_interval` | `50` | Auto-review patterns every N decisions |

All passed as keyword arguments to `AlignmentEnclave.create()`.

## Links

- [NSE.dev](https://nse.dev) — Full NSE platform documentation
- [PyPI](https://pypi.org/project/social-alignment/)
- [GitHub](https://github.com/HumanjavaEnterprises/nostralignment.app.OC-python.src)
- [ClawHub](https://clawhub.ai/u/vveerrgg)

License: MIT
