---
description: Salesforce CLI read-only usage rules for VAEA sandbox queries
globs:
  - "V3/**"
  - "scripts/apex/**"
  - "*.apex"
  - "**/sf-schema*"
  - "**/config_loader.py"
---

# Salesforce CLI Usage Rules (READ-ONLY)

**Purpose:** This project queries VAEA Salesforce sandboxes for ACM-AI pipeline development (schema discovery, sample data, validation). It is **NEVER** a deployment target. Source of truth for deploys lives in `/home/demi/gitrepo/vaea` (VAEA SF repo).

> **Enforcement:** Hard `deny` entries in `.claude/settings.json` block dangerous commands even under `--dangerously-skip-permissions`. Do not work around them with shell tricks.

## Allowed Orgs (read-only)

| Alias / Username | Purpose | Access Level |
|---|---|---|
| `demi.thathsara@vaea.vic.gov.au.demidev` | VAEA Dev sandbox — schema/data discovery for ACM-AI | **READ-ONLY** |

Any org not in this list is **forbidden**. If you cannot find the `--target-org` value here, **stop and ask**.

### Forbidden Orgs (hard block)

- `demi.thathsara@vaea.vic.gov.au.sit` (VAEA SIT)
- Any VAEA UAT sandbox, Production org, or unlisted alias

## Allowed `sf` Commands (read-only, no confirmation needed)

- `sf org display`, `sf org list`, `sf org list users`
- `sf data query --query "SELECT ..."` — SOQL reads only
- `sf data search --query "FIND ..."` — SOSL reads only
- `sf data export tree` — local export only
- `sf sobject describe`, `sf schema list sobjects`, `sf schema list fields`
- `sf project retrieve start` — metadata retrieve to local (never `deploy`)
- `sf apex run --file <file>` — read-only anonymous Apex only (see below)

## Forbidden `sf` Commands (ALWAYS ask first)

- `sf project deploy *` — any deploy, including `--dry-run` against non-allowlisted org
- `sf data create/update/delete/upsert/import`
- `sf apex run` with DML: `insert`, `update`, `delete`, `upsert`, `Database.execute*`, `Http` callouts, `System.enqueueJob/schedule`
- `sf org delete/create scratch/login`, `sf config set target-org`
- Anything with `--target-org` resolving to a non-allowlisted org

## Pre-flight Protocol (MANDATORY before every `sf` call)

1. **Print the exact command** you are about to run
2. **Resolve and print the target org** (`sf org display --target-org <alias>`)
3. **Classify**: SELECT SOQL / describe / display → OK. Anything else → **STOP, ask Demi**
4. **Never chain** a forbidden command in a pipeline (`&&`, `;`, `|`)

## SOQL Guardrails

- Always `LIMIT N` on exploratory queries (default `LIMIT 10`)
- Prefer `SELECT Id, Name, <fields>` over `SELECT FIELDS(ALL)`
- Never `UPDATE`, `DELETE`, `UPSERT` via Tooling API or REST from this repo

## Anonymous Apex Rules

- File must live under `scripts/apex/readonly/` named `ro_*.apex`
- File header: `// READ-ONLY — no DML, no callouts, no async enqueue`
- `grep` file for DML keywords before running — abort if any found

## Secrets & Auth

- Never commit: `.sf/`, `.sfdx/`, `demidev.json`, `*.key`, `*.pem`, or files with tokens/secrets
- If you see an auth artifact in a diff, **stop and warn Demi**

## Cross-Reference

Canonical VAEA Salesforce standards: `/home/demi/gitrepo/vaea/CLAUDE.md` and `/home/demi/gitrepo/vaea/knowledge-base/`
