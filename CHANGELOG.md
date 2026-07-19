# Changelog

## 0.1.6 — 2026-07-19

Reconciliation release. Two independent `0.1.5` lineages existed with different
content — one carrying the real five-lens compass implementation, the other a
standalone `clawhub/SKILL.md` rewrite. This release unifies both: it keeps the
compass code, tests, and packaging, and folds in the expanded SKILL.md
(operator guidance, agent-type metadata, per-lens reference). Because the two
`0.1.5` builds differed, a fresh version and republish are required.

### Changed

- Merged the SKILL.md documentation rewrite (Operator Guidance section,
  agentic-primitive frontmatter) on top of the compass implementation.
- Documentation reworded to plain functional language (removed the
  "sovereign entity" / "entity-aware" identity framing; the **Sovereign** lens
  name is unchanged). Example owner name standardized to `vergel`.
- Version bumped to `0.1.6` across `pyproject.toml`,
  `src/social_alignment/__init__.py`, `clawhub/metadata.json`, and
  `clawhub/SKILL.md`.

## 0.1.5 — 2026-07-19

First real build of the alignment pillar. Prior versions on PyPI (`0.1.0`,
`0.1.1`) and the reserved ClawHub `0.1.4` were an **empty placeholder shell**;
this release replaces that shell with a working package. Part of the
coordinated 2026-07 correctness release for the Nostr library family (staged,
pending PyPI/ClawHub publish).

### Added

- **Deterministic pre-action five-lens compass.** `AlignmentEnclave` evaluates
  a proposed action through five pure lenses — Builder (can I execute this
  reliably?), Owner (does this protect my human?), Defense (does this harden
  against threats?), Sovereign (do I stay well while my human is away?), and
  Partnership (does this strengthen trust?) — and aggregates them to the worst
  severity (`CLEAR < CAUTION < YIELD < STOP`), mapping to an escalation level
  (`NONE` / `INFORM` / `ASK` / `HALT`).
- `AlignmentEnclave.check(...)` returns a `CheckResult` (`should_proceed`,
  `should_escalate`, `projection`, `escalation`) and keeps an in-memory
  decision log via `record_proceeded()` / `record_deferred()`.
- A `STOP` always defers to the human: `record_proceeded()` after a STOP raises
  `RuntimeError` unless `owner_overrode=True`.
- Frozen dataclasses throughout (`ActionContext`, `LensResult`, `Projection`,
  `EscalationDecision`, `CheckResult`, `Decision`, `AlignmentConfig`).
- **Zero runtime dependencies** — the pillar installs standalone and does not
  require `nostrkey` or anything else.
- Orchestrator contract: `AlignmentEnclave.create(owner_npub=..., owner_name=...)`
  then `.check(domain=..., description=..., **context)`, filtering unknown
  kwargs so `nse-orchestrator` can pass a superset without a `TypeError`.

### Tests

- Known-answer and per-lens unit tests covering the five lens functions,
  severity aggregation, escalation mapping, and the STOP-defers-to-human
  invariant. The evaluation core is pure (no I/O, no randomness), so the same
  `ActionContext` always yields the same `CheckResult`.
