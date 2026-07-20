# CLAUDE.md — social-alignment

## What this is
A deterministic five-lens pre-action compass for AI agents. Part of the open-source OpenClaw Nostr toolkit. MIT licensed.

## Install
```
pip install social-alignment
```

## Develop
```
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
python -m pytest -q     # tests
python -m build         # sdist + wheel
```

## Layout
- `src/social_alignment/` — package source
- `tests/` — pytest suite
- `clawhub/` — ClawHub skill metadata (SKILL.md, metadata.json)

## Conventions
- Python + pyproject (hatchling). Pure-Python crypto (`cryptography`), zero native build deps.
- Public, MIT-licensed, open source.
