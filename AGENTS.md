# AGENTS.md

## Scope

This file defines mandatory working rules for AI/coding agents in this repository.

- Project root: `/workspace/steuerreport`
- Product: German crypto tax-report engine and dashboard
- Documentation language: German
- Code, identifiers, comments, and tests: English unless existing local context is German
- Active development branch: `codex/next-roadmap-work`
- Active GitHub PR: `#3`

Agents must read this file before making changes. For current project state, read
`docs/99_CHAT_HANDOFF_AKTUELL.md` next.

## Hard Product Rules

- German tax-law scope starts at tax year `2020`.
- PDF export must keep a hard maximum of `100` pages per PDF file.
- Raw data must never be deleted.
- Corrections must be implemented through documented imports, overrides, review actions, transfer matches, or audit scripts.
- Do not invent acquisition costs, prices, FX rates, cost basis, source evidence, or tax treatment.
- Do not describe results as tax-advisor-final. This project produces technical calculations and evidence packages.
- Historic open issues may be visible without blocking current-year export when the runtime gate explicitly marks years as closed, for example `runtime.review.closed_tax_years`.

## Data And Privacy

Never commit or push local primary data or generated local work artifacts.

Forbidden in Git:

- `*.csv`
- `*.xlsx`
- `var/`
- `*.db`
- `*.sqlite`
- `*.sqlite3`
- `.env`
- exchange exports, wallet exports, tax-office submissions, API responses with personal/account data

Before committing, verify that no raw or generated data is staged:

```bash
git diff --cached --name-only | rg '\.(csv|xlsx|db|sqlite|sqlite3)$|^var/' || true
git status --ignored --short | rg '^(!!|\?\?) (var/|.*\.(csv|xlsx|db|sqlite|sqlite3)$)' || true
```

If primary data is needed for analysis, use it locally only and document derived findings in `docs/`.

## Current Operational State

- Live dashboard uses port `8000`.
- Do not switch workflows to port `8001`.
- Current handoff: `docs/99_CHAT_HANDOFF_AKTUELL.md`.
- Current completion and GitHub sync report: `docs/216_CURRENT_AUTONOMOUS_COMPLETION_AND_GITHUB_SYNC_2026-05-10.md`.
- AI readonly database path:
  `/root/.local/share/steuerreport/ai_readonly/steuerreport_ai_readonly.sqlite`
- AI readonly queue status command:

```bash
python3 scripts/ai_readonly_task_queue.py status
```

The AI readonly queue is for evidence discovery and planning. Its findings are not automatic truth. Re-check important claims against the database or source files before changing code or review state.

## Git And GitHub

- Work on `codex/next-roadmap-work` unless the user explicitly changes branch.
- Keep PR `#3` aligned after meaningful commits.
- Prefer one coherent commit per validated work package.
- Do not force-push unless the user explicitly asks.
- Do not commit raw data, `var/`, local databases, local exports, or secrets.
- Use GitHub connector or `gh` for PR/issue state when available.
- If `gh` is not authenticated, use the GitHub connector for metadata and local `git` for branch/remote state.

Before push:

```bash
git status --short --branch
git diff --check
git diff --cached --name-only | rg '\.(csv|xlsx|db|sqlite|sqlite3)$|^var/' || true
```

## Validation Gates

Run the narrowest relevant tests while developing. Before committing broad workflow changes, run:

```bash
python3 -m ruff check . --no-cache
python3 -m mypy src/ --cache-dir=/tmp/steuerreport_mypy_cache
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m pytest -q tests/unit
COVERAGE_FILE=/tmp/steuerreport-api-coverage PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m pytest -p no:cacheprovider tests/unit/api --cov=src/tax_engine/api --cov-fail-under=80 -q
node --check src/tax_engine/ui/static/app.js
python3 scripts/verify_integrity.py --all-years
```

If a gate cannot be run, document why and run the closest lower-risk substitute.

## Architecture And Coding Rules

- Prefer existing project patterns over new abstractions.
- Keep tax logic deterministic, auditable, and Decimal-safe.
- Use Pandas where the surrounding ingestion/audit workflow already uses it.
- Keep FIFO and derivatives logic separate; do not mix spot inventory and derivative PnL paths.
- Preserve deque/FIFO behavior unless explicitly changing the tax method.
- Keep raw-event payloads immutable. Add derived state through normalized rows, review actions, settings, or documented overrides.
- Keep API compatibility re-exports in `tax_engine.api.app` when tests or external callers import them from there.
- For standalone scripts under `scripts/`, project-local bootstrap imports using `sys.path` are allowed. Ruff `E402` is ignored for `scripts/*.py`.
- Use structured parsing for CSV/XLSX/JSON. Avoid brittle string parsing when a proper parser exists.
- Do not add broad refactors while fixing a narrow tax or import issue.

## Database And Runtime State

- Use testing environment variables for tests that reset the store:

```bash
STEUERREPORT_ENV=testing STEUERREPORT_DB_PATH=/tmp/steuerreport/steuerreport_test.db
```

- Do not run destructive DB operations on live/local project data unless explicitly requested.
- Prefer read-only SQLite URI for evidence checks:

```bash
sqlite3 'file:/root/.local/share/steuerreport/ai_readonly/steuerreport_ai_readonly.sqlite?mode=ro&immutable=1'
```

- Rebuild readonly snapshots only through the documented scripts when needed.

## Documentation Rules

- Major findings, fixes, and decisions must be documented under `docs/`.
- Keep `docs/99_CHAT_HANDOFF_AKTUELL.md` current after significant work.
- New audit/status documents should use the next numeric prefix and an explicit date, for example:
  `docs/217_SHORT_TOPIC_2026-05-10.md`.
- Summaries must distinguish:
  - deterministic fix
  - evidence gap
  - unsafe action
  - remaining manual review
- Do not delete old docs unless the user explicitly asks. Mark superseded findings in newer docs instead.

## Review And Tax Safety

When resolving tax issues:

- Identify the latest completed job for the relevant tax year.
- Check whether an issue is current-year blocking or historic-only.
- Validate zero-cost findings against `ai_open_zero_cost_tax_lines` or the current processing output.
- For transfer-chain fixes, document event IDs, timestamps, assets, quantities, source files, and match IDs.
- For price or FX backfills, document source, date, asset, rate, and why it is acceptable.
- For manual decisions, include required evidence and reviewer-facing rationale.
- Never close a review issue only because it is inconvenient. Close it only if the data or explicit project rule supports it.

## Frontend Rules

- The dashboard is an operational tool, not a landing page.
- Important controls must be visible inside the relevant dashboard section, not hidden only in a global header.
- Keep UI dense, readable, and review-oriented.
- Avoid decorative redesigns that do not improve review, import, export, or reconciliation workflows.
- Validate JavaScript syntax with:

```bash
node --check src/tax_engine/ui/static/app.js
```

## Agent Workflow

Default behavior:

1. Read `AGENTS.md`.
2. Read `docs/99_CHAT_HANDOFF_AKTUELL.md`.
3. Check `git status --short --branch`.
4. Inspect current GitHub PR/issue state when the task touches sync or release.
5. Work directly when the user request is clear.
6. Ask only when a decision is risky, not discoverable locally, or requires explicit tax/evidence judgment.
7. Validate.
8. Document.
9. Commit and push only the GitHub-safe scope when asked to sync or when the task clearly includes GitHub sync.

Do not stop at a plan when the user asked for execution. If blocked, leave exact evidence, commands, and the next safe action.
