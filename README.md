# funedistri-module

Custom Odoo module **`funedistri_customizations`** for
[Funedistri](https://funedistri.odoo.com) — a B2B coffin shop on Odoo.sh. It lets
the Owner define configurable coffins (native Product Attributes) in the backend
and lets approved B2B users build and submit them as Pending Orders, with
role-based price visibility.

This repo **is** the Odoo.sh addons repo: `git push` → Odoo.sh deploys.

> **Status (2026-06-15):** the module was reset to an empty, installable shell and
> is being rebuilt step by step. See `docs/IMPLEMENTATION_PLAN.md`.

## Local dev

Requires Docker Desktop running.

```sh
make dev     # boot Postgres + Odoo, install the module + local seed, dev mode
             # → http://localhost:8069  (login: admin / admin)
make down    # stop containers (Postgres data kept)
make reset   # drop the dev database for a clean slate
make logs    # tail Odoo logs
```

The local-only `funedistri_dev_seed` module (installed by `make dev`, never on
prod) seeds test data. Odoo's global demo data stays off.

## Docs

- `CLAUDE.md` — project instructions + design decisions index.
- `CONTEXT.md` — ubiquitous language (glossary).
- `docs/IMPLEMENTATION_PLAN.md` — the step-by-step build order.
- `docs/FEATURE_MAP.md` — feature → files map (ADR 0006: one module, by feature).
- `docs/adr/` — architecture decision records.
