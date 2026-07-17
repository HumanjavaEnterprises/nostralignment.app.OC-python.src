# social-alignment

A deterministic pre-action **five-lens compass** for sovereign AI agents. The
alignment pillar of the NSE platform. Before an agent takes a significant
action, five lenses evaluate it and the enclave decides whether to proceed,
inform, ask, or halt.

**Import:** `pip install social-alignment` → `from social_alignment import AlignmentEnclave`

Zero runtime dependencies. Does **not** depend on `nostrkey`.

## Build & Test

```bash
pip install -e ".[dev]"
ruff check .
pytest -q
```

## Structure

- `src/social_alignment/` — package source
  - `types.py` — enums (`ActionDomain`, `Lens`, `Severity`, `EscalationLevel`) and frozen
    dataclasses (`ActionContext`, `LensResult`, `Projection`, `EscalationDecision`,
    `CheckResult`, `Decision`, `AlignmentConfig`)
  - `enclave.py` — the five pure lens functions, `_aggregate`, `_escalate`, `evaluate`,
    and `AlignmentEnclave` (main entry point + in-memory decision log)
- `tests/` — pytest suite (known-answer + per-lens unit tests)
- `examples/basic_usage.py` — runnable example
- `clawhub/` — OpenClaw skill metadata

## Publish

```bash
# PyPI (needs API token + OTP)
python3 -m build
python3 -m twine upload dist/social_alignment-X.Y.Z*

# ClawHub
npx clawhub publish ./clawhub --slug social-alignment --name "Social Alignment" \
  --version X.Y.Z --tags latest --changelog "..."
```

**Version must be bumped in 3 places:** `pyproject.toml`, `src/social_alignment/__init__.py`
(`__version__`), and `clawhub/metadata.json`.

> Note: PyPI already carries `0.1.0` and `0.1.1`; ClawHub metadata had reserved `0.1.4`.
> This build is `0.1.5` to stay ahead of all reserved versions.

## Conventions

- Python 3.10+, hatchling build, ruff linter (100 char line length)
- **Zero runtime dependencies.** Do not add any — this pillar must install standalone.
- Import matches package name: `pip install social-alignment` → `from social_alignment import ...`
- The five lenses are pure functions: same `ActionContext` + `AlignmentConfig` → same result.
- Severity ordering (`IntEnum`): `CLEAR=0 < CAUTION=1 < YIELD=2 < STOP=3`. Aggregate = max.
- `STOP` always defers to the human: `record_proceeded()` on a STOP without
  `owner_overrode=True` raises `RuntimeError`. Enforced in code, no workaround.
- `AlignmentEnclave.create(owner_npub=..., owner_name=..., **overrides)` filters unknown
  overrides against `AlignmentConfig` fields — the orchestrator passes a superset and must
  never trigger a `TypeError`. `check(...)` filters unknown context kwargs the same way.
- Decision log is in-memory only (no persistence in this minimal build).
- Frozen dataclasses everywhere in `types.py`.

## Orchestrator contract

`nse-orchestrator`'s `entity.py` calls
`AlignmentEnclave.create(owner_npub=..., owner_name=...)` then
`.check(domain=..., description=..., **context)`. The orchestrator's `alignment` extra already
references `social-alignment`; no orchestrator code change is needed.
