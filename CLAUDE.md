# Funedistri coffin configurator — Odoo module

Custom Odoo module for **Funedistri**, a B2B coffin e-commerce business running on Odoo.sh.

# Context

- Existing Odoo e-commerce site selling coffins B2B: https://funedistri.odoo.com
- Only B2B users approved by the owner can log in and shop.
- Today coffins are **pre-configured** (wood, details…) and users pick a finished product.
- Hosted on Odoo.sh.

# Goal

Let the owner configure, from the **Odoo backend**, all coffin options and their prices — e.g. wood (oak, plywood… → dropdown), engraving (yes/no + text), and a longer list besides — then expose these configurable "base" coffins in the catalog so approved B2B users can build one and place an order.

The detailed, resolved design is under **Design decisions** below.

# Guidelines

- ALWAYS explain in comments what the code does and WHY. I'm new to Python and Odoo, so I need this information.

# Terminology / Naming rules

- **Funedistri** = the business selling coffins (the company that owns the Odoo site).
- **Owner** = the person running Funedistri. The ONLY user who accesses the **Odoo backend**. Configures coffin options, validates orders, ships.
- **B2B user** = a customer user. Logs into the **e-commerce website frontend ONLY** — never the Odoo backend. Belongs to a customer company. Two roles:
  - **SALESMAN** — places orders on behalf of their company. Sees **NO prices** anywhere (product, cart, checkout, emails, portal history).
  - **STORE_OWNER** — places orders. **Sees prices.**
- "Place an order" = checkout that creates a draft sale order (no payment). The owner manually validates + ships.

# Design decisions (grilling session 2026-06-07)

## Repo & deployment
- This repo **becomes the Odoo.sh addons repo**. The module lives in the repo, `git push` → Odoo.sh deploys. No separate copy step; local dev mirrors prod.
- **Odoo version = 19 (ASSUMED, NOT verified).** ⚠️ MUST confirm the real version of `funedistri.odoo.com` before any deploy — wrong version = module won't load. (Backend → Settings → footer.)

## Coffin configurator = HYBRID (native attributes + thin custom website layer)
The owner needs a long list of options, some priced, some informational, with image choices, a date field, and one-level conditional show/hide. Native Odoo covers most of it; a small custom layer fills the gaps.

- **Priced / discrete options** (wood, handles…) → native **product attributes & variants**.
  - Use **"no variant" mode** (don't auto-create SKU variants) → avoids combinatorial DB explosion; the selection is captured on the sale order line.
  - **Image dropdowns** → native "Image" display type on attribute values. ✅ native.
- **Engraving text** → native **"custom value"** attribute (free text on the order line) **+ a custom constraint** for the ≤20-char rule (native custom value has no length validation).
- **Date picking** → ❌ NOT native. A small **custom** field on the website form, stored on the order line.
- **Conditional logic** → confirmed **one-level only** (pick X → show/enable field Y). ❌ not native (native only has exclusion rules). A small **custom JS** snippet on the product page. Can hide OR disable the field — it just annotates a selected option.
- Output of checkout = a **draft sale order** (see Order workflow).
- All of this runs on the **website frontend** (`website_sale`), because B2B users never touch the backend.

## Roles & price visibility
- See Terminology. Owner = backend only. SALESMAN / STORE_OWNER = portal users, frontend only.
- **SALESMAN**: sees **NO price anywhere** — product, cart, checkout, confirmation emails, portal order history.
- **STORE_OWNER**: sees prices.
- A SALESMAN orders **on behalf of their company**; the price materializes for the owner / store-owner at validation.
- Price-hiding is a **real secret** (must not be fetchable via dev tools / raw requests), not cosmetic → enforce in the ORM, not just templates.
- **Role storage = field-drives-group.** The owner edits one `b2b_role` Selection field (`salesman` / `store_owner`) on the contact. A `write()` override silently syncs the underlying hidden security group (`coffin_salesman_group` / `coffin_store_owner_group`). The owner gets a simple dropdown; we get **record-rule + field-level enforcement** so a SALESMAN physically cannot query a price.
- **Granularity = per user** (a company can have one STORE_OWNER + several SALESMEN).
- **Company-scoped order visibility is NATIVE** — standard portal record rules limit a portal user to their own `commercial_partner_id`'s documents. Requirement: all B2B users of a company must be **contacts under the same parent company** (`res.partner`) so they share a `commercial_partner_id`. This is data setup, not code.

## Order workflow (flow A)
- Checkout has **no online payment**. The final step is a custom **"Submit order"** button (not "Pay now").
- Submitting creates a **sale order in quotation/draft state**, assigned to the B2B user's company.
- **The B2B user sees** an "Order received — pending approval" confirmation page; the order appears in their portal history as *Quotation/Pending* (never "paid").
- **The owner can fully edit the draft** (options, price, quantities) before confirming — important because a SALESMAN built it blind to price.
- **The owner is notified** on each submit (email/activity) so no order sits unseen.
- No credit terms / order minimums / approval rules for now — plain submit-and-approve.

## Do I need the owner's existing Odoo codebase here?
- **No** — not needed to build the module. Just declare the proper dependencies (`website_sale`, `sale`). Optionally pull a production DB dump later for realistic testing.

## Module name
- Technical name = **`funedistri_coffin_configurator`** (folder name + manifest). Hard to rename later.

## Local dev setup (`make dev`)
- **Docker Compose**: official `odoo:19` image + `postgres:16` (Odoo 19 needs PG 14+). `docker compose up`.
- **`make dev`** = boot Postgres + Odoo, create a fresh DB, **auto-install the module + deps** (`website_sale`, `sale` via manifest `depends`), run in dev mode (`--dev=all`, hot-reload of XML/Python).
- **Repo layout**: the module dir(s) at the **repo root** (Odoo.sh treats each top-level dir with `__manifest__.py` as a module). Dev-only files (`Makefile`, `docker-compose.yml`, `odoo.conf`) sit alongside; Odoo.sh ignores anything without a manifest.
- **Demo seed = YES** (Odoo `demo` data, loads only in the dev DB, never prod): one customer company + one SALESMAN + one STORE_OWNER portal user + one configurable coffin with a few priced/image/text/date options. So every `make dev` gives a clickable store to test roles + config.

# Open questions (next session)
1. **Verify the real Odoo version** of `funedistri.odoo.com` (currently assuming 19).
2. Confirm whether a prod DB dump is wanted for local testing (default: no — the demo seed is enough to start).
