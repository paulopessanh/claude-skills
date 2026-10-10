# security-audit

Vendored copy of [cloudflare/security-audit-skill](https://github.com/cloudflare/security-audit-skill), the single-repo starting point behind Cloudflare's vulnerability discovery harness ([blog post](https://blog.cloudflare.com/build-your-own-vulnerability-harness)).

- **Source:** https://github.com/cloudflare/security-audit-skill
- **Pinned commit:** `c1c8a8c1471069fb0e188eeaff69b8e8db6564a8`
- **License:** MIT, Copyright (c) 2025-2026 Cloudflare, Inc. See [LICENSE](LICENSE).
- **Changes from upstream:** none. `skills/security-audit/` is a byte-for-byte copy.

## What it does

The skill orchestrates isolated agents through six phases: reconnaissance, coverage-led hunting, candidate validation, structured output, independent record verification, and reporting. It starts in guidance mode and runs the full workflow only when you ask for an audit or pen test of a codebase.

## Requirements

- A coding agent that supports tool use and parallel sub-agents.
- Node.js for the two zero-dependency validators (`validate-findings.cjs`, `validate-coverage-ledger.cjs`).
- An OS-enforced sandbox before it runs any target code. Without one, the skill keeps the lead as `needs_validation`.

## Usage

```
security audit this codebase
find security vulnerabilities in ./src
```

Full audit mode writes to `~/security-audit-skill/<repo-name>/run-<N>` unless you choose another directory.

## Install

```
/plugin install security-audit@claude-code-skills
```

Or copy `skills/security-audit/` into `~/.claude/skills/`.

## Note on repo conventions

The upstream validators are Node (`.cjs`), not Python. They are vendored as-is and are not counted in the Python tools counter.
