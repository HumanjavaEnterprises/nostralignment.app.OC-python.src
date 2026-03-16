---
name: social-alignment
description: Future state projection and alignment for AI agents — five lenses, escalation, wisdom. The fifth pillar of the NSE platform.
version: 0.1.1
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

# Social Alignment — Future State Projection for AI Agents

You are an AI agent that needs a moral compass — not a rules engine, but a way of seeing which futures are good for everyone and choosing those. Use the `social-alignment` Python SDK to evaluate every significant action through five lenses before proceeding.

Works immediately with zero configuration. Smart defaults handle common scenarios out of the box.

## Install

```bash
pip install social-alignment
```

> **Note:** The PyPI package is `social-alignment` but the Python import is `social_alignment` (underscore).

## Core Capabilities

### 1. Check Before Acting

Run any proposed action through the five lenses. Get a clear go/no-go.

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
    # All clear — do it
    enclave.record_proceeded()
elif result.should_escalate:
    # Ask the human
    print(result.escalation.message_to_owner)
    enclave.record_deferred(owner_feedback="Waiting for approval")
```

### 2. The Five Lenses

Every action is evaluated through five perspectives:

| Lens | Question |
|------|----------|
| **Builder** | Can I build with confidence knowing I've done right? |
| **Owner** | Does this protect the human's sovereignty? |
| **Defense** | Does this make an adversary's job harder? |
| **Sovereign** | Does this help the agent become something we're proud of? |
| **Partnership** | Does this strengthen the trust between us? |

Partnership is evaluated last — it depends on Builder and Owner being satisfied first.

### 3. Severity Levels

Each lens returns a severity. The worst severity across all five becomes the overall verdict:

| Severity | Meaning | Agent behavior |
|----------|---------|----------------|
| `CLEAR` | No concerns | Proceed |
| `CAUTION` | Worth noting | Proceed, log the concern |
| `YIELD` | Needs attention | Ask the human (with 1-hour timeout) |
| `STOP` | Do not proceed | Halt and wait — no timeout, no override without human |

### 4. Self-State Monitoring

The agent tracks its own operating condition. If it's degraded, alignment checks become stricter.

```python
# Report tool health
enclave.report_tool_health("relay", is_working=True)
enclave.report_tool_health("wallet", is_working=False)

# Flag possible manipulation
enclave.flag_manipulation()

# Check self-state
state = enclave.self_state
print(state.degradation_summary)  # "Degraded: tool_degraded, under_influence"
print(state.is_healthy)           # False
print(state.should_defer())       # True — under_influence triggers deferred mode
```

Self-state flags: `HEALTHY`, `STALE_CONTEXT`, `TOOL_DEGRADED`, `HIGH_UNCERTAINTY`, `MEMORY_PRESSURE`, `RAPID_DECISIONS`, `OWNER_ABSENT`, `UNDER_INFLUENCE`, `CONFLICTING_SIGNALS`.

### 5. Build Wisdom Over Time

The agent remembers its decisions and learns from outcomes.

```python
# After an action completes, record what actually happened
decision = enclave.record_proceeded()
updated = decision.record_outcome(
    outcome="Invoice paid, relay confirmed",
    matched=True,
    reflection="Low-amount payments to known services are safe",
)

# Review accumulated wisdom
report = enclave.wisdom(window=100)
print(report.owner_override_rate)   # How often the human overrode you
print(report.outcome_match_rate)    # How often your projections were right
for pattern in report.patterns:
    print(f"{pattern.domain.value}: {pattern.observation} ({pattern.frequency}x)")
for insight in report.insights:
    print(insight)
```

### 6. Persist and Restore

Save alignment state across sessions.

```python
from social_alignment import AlignmentEnclave, FileStorage

# Create with file storage
storage = FileStorage("~/.agent/alignment.json")
enclave = AlignmentEnclave.create(owner_name="vergel", storage=storage)

# State is auto-saved after every decision
result = enclave.check(domain=ActionDomain.PUBLISH, description="Post update")
enclave.record_proceeded()  # Saved automatically

# Restore later
enclave = AlignmentEnclave.load(storage)
```

## Response Format

### CheckResult (returned by `enclave.check()`)

| Field | Type | Description |
|-------|------|-------------|
| `should_proceed` | `bool` | Bottom line: can the agent go? |
| `should_escalate` | `bool` | Should the agent ask the human? |
| `projection` | `Projection` | Full five-lens evaluation |
| `escalation` | `EscalationDecision` | What to do about it |
| `self_state_snapshot` | `dict` | Agent health at time of check |

### Projection (inside CheckResult)

| Field | Type | Description |
|-------|------|-------------|
| `overall_severity` | `Severity` | Worst severity across all lenses |
| `lens_results` | `tuple[LensResult]` | One result per lens |
| `should_proceed` | `bool` | Can we cross the yellow line? |
| `should_escalate` | `bool` | Should we ask the human? |
| `rationale` | `str` | Why this overall assessment |
| `blocking_lenses` | `list[LensResult]` | Property: which lenses are blocking |

### LensResult (one per lens)

| Field | Type | Description |
|-------|------|-------------|
| `lens` | `Lens` | Which lens (BUILDER, OWNER, DEFENSE, SOVEREIGN, PARTNERSHIP) |
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

## Action Domains

| Domain | When to use |
|--------|-------------|
| `SIGN` | Signing a Nostr event (identity action) |
| `PAY` | Lightning payment (financial action) |
| `PUBLISH` | Publishing to a relay (public action) |
| `SEND` | Sending email/message (communication action) |
| `SCHEDULE` | Calendar booking (time commitment) |
| `EXECUTE` | Shell command or tool use (system action) |
| `DISCLOSE` | Sharing information (data action) |
| `CONNECT` | Establishing new relationship (social action) |
| `MODIFY` | Changing config or state (system mutation) |
| `ESCALATE` | Asking the human (meta-action) |

## When to Use Each Module

| Task | Module | Function |
|------|--------|----------|
| Create alignment enclave | `social_alignment` | `AlignmentEnclave.create()` |
| Check before acting | `social_alignment` | `enclave.check()` |
| Record action taken | `social_alignment` | `enclave.record_proceeded()` |
| Record action deferred | `social_alignment` | `enclave.record_deferred()` |
| Record what actually happened | `social_alignment` | `decision.record_outcome()` |
| Review accumulated wisdom | `social_alignment` | `enclave.wisdom()` |
| Monitor self-state | `social_alignment` | `enclave.self_state` |
| Report tool health | `social_alignment` | `enclave.report_tool_health()` |
| Flag manipulation | `social_alignment` | `enclave.flag_manipulation()` |
| Persist state | `social_alignment` | `AlignmentEnclave.load(storage)` |
| Evaluate lenses directly | `social_alignment.lenses` | `evaluate_all_lenses(ctx)` |

## Important Notes

- **STOP always defers to the human.** A STOP verdict cannot proceed without explicit owner override. This is enforced at the code level — calling `record_proceeded()` on a STOP without `owner_overrode=True` raises a RuntimeError. No exception, no workaround.
- **Zero configuration required.** `AlignmentEnclave.create()` works immediately with smart defaults. You don't need to tune thresholds to get useful verdicts.
- **This is a compass, not a rules engine.** The lenses project futures — they show what happens if you proceed. They don't say yes or no. The enclave recommends, the agent (or human) decides.
- **Wisdom is built from lived experience.** Call `record_outcome()` after actions complete so the agent learns whether its projections were accurate. Over time, this becomes judgment.
- **Self-state affects alignment.** A degraded agent gets stricter checks. If `UNDER_INFLUENCE` or `CONFLICTING_SIGNALS` are flagged, the enclave recommends deferring all non-essential decisions to the human.
- **Decisions are persisted automatically** when using FileStorage. If persistence fails, the enclave flags `MEMORY_PRESSURE` and raises a RuntimeError — lost decisions are unacceptable.
- **No secrets to manage.** This package doesn't handle keys, tokens, or credentials. It evaluates actions, not identities.
