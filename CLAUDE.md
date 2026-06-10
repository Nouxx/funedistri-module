# Funedistri coffin configurator — Odoo module

Custom Odoo integration for **Funedistri**, a B2B coffin e-commerce business running on Odoo.sh.

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

> Canonical ubiquitous language lives in `CONTEXT.md` (glossary, no implementation). Key terms: **Coffin model** (catalog template) vs **Configured coffin** (built instance on a line); **Order** (never "quotation"); **Validate** (the Owner's accept verb — not confirm/approve); states **Pending → Validated → Shipped**.

## Domain ↔ Odoo v19 model mapping

⚠️ Standard Odoo v19 knowledge, NOT yet verified against the running instance (no module installed locally). Re-check at scaffold — esp. `sale.order.state` (the enum changed in v17: old `done` removed).

| Domain term | Odoo v19 model / field | Notes |
|---|---|---|
| Coffin model | `product.template` | configurable product; options as **"no variant"** attributes |
| Options (the choices) | `product.attribute` + `product.attribute.value` | linked to template via `product.template.attribute.line` |
| Option price | `product.template.attribute.value.price_extra` | |
| Configured coffin | `sale.order.line` | carries `product_no_variant_attribute_value_ids` + `product_custom_attribute_value_ids` |
| Engraving text | `product.attribute.custom.value` (native) | ≤20-char constraint is custom |
| Death date / Delivery date | custom date fields on `sale.order.line` | no native model |
| Order | `sale.order` | |
| **Pending** state | `sale.order.state = 'draft'` | Odoo label "Quotation"; we never say "quotation" |
| Owner **Validates** | `sale.order.action_confirm()` → `state = 'sale'` | we skip the `'sent'` state — never email a quote to a price-blind salesman |
| **Shipped** | ⚠️ NOT a `sale.order` state | needs `stock`/delivery; **out of scope for now**, informal owner-tracked |
| Owner / B2B user | `res.users` | |
| Customer company / contacts | `res.partner` (+ `commercial_partner_id`) | all B2B users of a company share one parent → native company-scoped visibility |
| `b2b_role` | Selection field on `res.partner` | drives the security groups via `write()` sync |
| Salesman / Store owner groups | `res.groups` | `coffin_salesman_group` / `coffin_store_owner_group` |
| Owner notification | `mail.activity` (+ mail template) | activity primary, email nudge |

# Design decisions (grilling session 2026-06-07)

## Repo & deployment
- This repo **becomes the Odoo.sh addons repo**. The module lives in the repo, `git push` → Odoo.sh deploys. No separate copy step; local dev mirrors prod.
- **Odoo version: prod (funedistri.odoo.com on Odoo.sh) = 19.2; local dev image `odoo:19` reports series 19.0** (verified at Step 0 scaffold, 2026-06-10). The community `odoo:19` image is the 19.0 generation — local does NOT mirror prod at the series level.
  - **Manifest version = short form `1.0.0`** (NOT `19.x.*`). A series-prefixed version that mismatches the running server makes Odoo set `installable=False` ("incompatible version"). The short form lets Odoo auto-prepend whichever series loads it, so the module installs on BOTH 19.0 (local) and 19.2 (prod). See `funedistri_coffin_configurator/__manifest__.py`.

## Coffin configurator = HYBRID (native attributes + thin custom website layer)
The owner needs a long list of options, some priced, some informational, with image choices, a date field, and one-level conditional show/hide. Native Odoo covers most of it; a small custom layer fills the gaps.

- **Priced / discrete options** (wood, handles…) → native **product attributes & variants**.
  - Use **"no variant" mode** (don't auto-create SKU variants) → avoids combinatorial DB explosion; the selection is captured on the sale order line.
  - **Image dropdowns** → native "Image" display type on attribute values. ✅ native.
- **Engraving text** → native **"custom value"** attribute (free text on the order line) **+ a custom constraint** for the ≤20-char rule (native custom value has no length validation).
- **Date picking** → ❌ NOT native. Custom date field(s) per line, stored on `sale.order.line` (refined 2026-06-10).
  - **Design goal = FLEXIBLE, not a fixed schema.** Any date field must be **optional**, and a choice in the form may **imply / reveal other fields** (one-level conditional, see below). Dates are just one kind of conditionally-shown field.
  - Concrete examples (NOT an exhaustive or frozen list):
    - **Death date** — deceased's date of death, **engraved on the coffin plate**.
    - **Delivery date** — deadline the SALESMAN needs the order by. Not engraved.
  - Captured on the website product/checkout form, flow onto the draft order line for the owner.
  - **RESOLVED (2026-06-10): dev-defined but generic.** Custom date/text/yes-no fields live in CODE (dev adds a new one). But each is **optional**, and the conditional-reveal mechanism is **generic** — any field can be wired to any trigger via small config, no rewrite per rule. Adding a brand-new field type = a dev touch (acceptable; these change rarely). The frequently-changing part — priced dropdown options — stays owner-self-serve via native attributes. Owner does NOT get a meta-configurator UI to invent fields. Keeps the custom layer thin.
- **Conditional logic** → confirmed **one-level only** (pick X → show/enable field Y). ❌ not native (native only has exclusion rules). Mechanism (refined 2026-06-10):
  - **Rules = single source of truth in Python/data** (e.g. on the attribute value / a config record). The product page renders them into the DOM (data attributes); a small **custom JS** snippet consumes them to show/hide/disable fields. NO rule duplicated in JS.
  - The **server reads the SAME rules** to validate. JS = UX only; server = truth.
  - **Required-when fields validated server-side** (controller / `@api.constrains`), even though price-hiding is only "practical." Reason: a missing required field (e.g. death date when engraving=yes) = a broken draft the owner ships blind — this is **data integrity**, not price secrecy, so it must not be client-side-only.
- Output of checkout = a **draft sale order** (see Order workflow).
- All of this runs on the **website frontend** (`website_sale`), because B2B users never touch the backend.

## Roles & price visibility
- See Terminology. Owner = backend only. SALESMAN / STORE_OWNER = portal users, frontend only.
- **SALESMAN**: sees **NO price anywhere** — product, cart, checkout, confirmation emails, portal order history.
  - **One checkout flow for both roles** (decided 2026-06-10). Price elements masked for SALESMAN via a **server-rendered placeholder** (e.g. `XXXX €` / "Prix masqué") + a **tooltip** explaining why it's hidden. Payment step → "Submit order" for everyone (flow A).
  - ⚠️ Masking MUST be server-side: for a SALESMAN the server renders the placeholder and **never emits the real number** — not in the HTML, not in the JSON cart/checkout routes. A CSS/JS cover over a real number in the DOM = FAILS even the practical bar (Q2). So: QWeb `has_group()` swaps number→placeholder, AND the website_sale JSON routes are overridden to strip/zero amounts for salesman.
  - UI locale = **French** (site sells in euros; tooltips/labels in FR).
  - **Email + PDF price suppression branches on the RECIPIENT / order partner `b2b_role`, NOT `env.user`** (decided 2026-06-10). Emails fire from system/owner context and the PDF can be generated by the owner — so `has_group(env.user)` is wrong at render time; key off the order's partner role instead.
    - **Salesman confirmation email = bare** "Order received — pending validation", NO line/price table at all. Zero leak risk, no masking logic in mail. (Owner gets a separate notification *with* price — next session.)
    - **Quote PDF: blocked for salesman** (access check on the portal report route), not a custom price-free report. Salesman never needs a priced quote.
- **STORE_OWNER**: sees prices.
- A SALESMAN orders **on behalf of their company**; the price materializes for the owner / store-owner at validation.
- Price-hiding for SALESMAN = **practical, not adversary-proof** (decided 2026-06-10). Price must never be *rendered* to a SALESMAN in normal use — product page, cart, checkout, confirmation email, portal order history, quote PDF — and not sit trivially in JSON route responses. We do NOT defend against a determined SALESMAN with dev tools reconstructing a number. Scope = suppress at the rendering + main JSON-route surface, accept residual leakage isn't worth the fragility of full ORM-level field hiding across every `website_sale` route.
- **Role storage = field-drives-group** (kept 2026-06-10). The owner edits one `b2b_role` Selection field (`salesman` / `store_owner`) on the contact. A `write()` override silently syncs the underlying hidden security group (`coffin_salesman_group` / `coffin_store_owner_group`). The owner gets a simple dropdown; we get a clean, idiomatic `request.env.user.has_group('...')` hook to branch price rendering in QWeb templates AND in website_sale JSON controllers. Groups (not a raw field read) chosen so the check is cache-friendly + conventional, and leaves the door open to tighten toward strict ORM enforcement later. Enforcement level today = **practical render/JSON suppression**, not the original "physically cannot query" claim.
- **Granularity = per user** (a company can have one STORE_OWNER + several SALESMEN).
- **Company-scoped order visibility is NATIVE** — standard portal record rules limit a portal user to their own `commercial_partner_id`'s documents. Requirement: all B2B users of a company must be **contacts under the same parent company** (`res.partner`) so they share a `commercial_partner_id`. This is data setup, not code.

## Order workflow (flow A)
- Checkout has **no online payment**. The final step is a custom **"Submit order"** button (not "Pay now").
- Submitting creates a **sale order in quotation/draft state**, assigned to the B2B user's company.
- **The B2B user sees** an "Order received — pending validation" (FR "en attente de validation") confirmation page; the order appears in their portal history as *Pending* (never "paid", never "quotation"). NB: "approval" is reserved for account access only — orders are **validated**, not approved.
- **The owner can fully edit the draft** (options, price, quantities) before confirming — important because a SALESMAN built it blind to price.
- **The owner is notified** on each submit — **both, activity primary** (decided 2026-06-10):
  - **Activity** ("To validate") scheduled on the new draft `sale.order`, assigned to the owner — durable native to-do, clicks to the order, stays until acted on. This is the "no order sits unseen" guarantee.
  - **Email** as a nudge to come look (owner not always in the backend).
  - Both fired in the Submit-order controller override (`activity_schedule()` + mail template).
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
1. **Verify the real Odoo version** of `funedistri.odoo.com`. CONFIRMED: 19.2 (2026-06-10).
2. Confirm whether a prod DB dump is wanted for local testing (default: no — the demo seed is enough to start).
