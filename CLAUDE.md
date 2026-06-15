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
- **One module, organised by feature.** All features live in `funedistri_customizations` (NOT split into separate modules — see ADR 0006). Inside it, prefer one file per feature within each Odoo layer folder. The feature→files map is `docs/FEATURE_MAP.md` — keep it current when adding/moving a feature.

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
| Engraving text | native **`product.attribute.custom.value`** (an `is_custom` attribute value) | v1: free text on the line, NO length limit; Owner trims at Validate. No custom field. (ADR 0004) |
| Death date / Delivery date | native **`product.attribute.custom.value`** (free text) | v1: free-text `is_custom` values, NOT typed Date fields, NO validation. Owner reads/corrects at Validate. (ADR 0004) |
| Backend visibility of the above | native | `is_custom` values show on the order line natively — no inherited view needed. The retired custom-field columns in `views/sale_order_views.xml` are removed. |
| Order | `sale.order` | |
| **Pending** state | `sale.order.state = 'draft'` | Odoo label "Quotation"; we never say "quotation" |
| Owner **Validates** | `sale.order.action_confirm()` → `state = 'sale'` | we skip the `'sent'` state — never email a quote to a price-blind salesman |
| **Shipped** | ⚠️ NOT a `sale.order` state | needs `stock`/delivery; **out of scope for now**, informal owner-tracked |
| Owner / B2B user | `res.users` | |
| Customer company / contacts | `res.partner` (+ `commercial_partner_id`) | all B2B users of a company share one parent → native company-scoped visibility |
| `b2b_role` | Selection field on `res.partner` | drives the security groups via `write()` sync |
| Salesman / Store owner groups | `res.groups` | `coffin_salesman_group` / `coffin_store_owner_group` |
| Owner notification | `mail.activity` (+ mail template) | activity primary, email nudge |

# Design decisions

> **Source of truth = `docs/adr/` (ADRs) + `CONTEXT.md` (glossary).** The build
> order is `docs/IMPLEMENTATION_PLAN.md`; the feature→files map is
> `docs/FEATURE_MAP.md`. The notes below are background/rationale that predate the
> 2026-06-15 reset — where an ADR exists it wins. (ADR index: 0001 price hiding ·
> 0003 portal/login gate · 0004 native-only config, no reveal · 0005 locked address
> book · 0006 single module by feature.)

## Repo & deployment
- This repo **becomes the Odoo.sh addons repo**. The module lives in the repo, `git push` → Odoo.sh deploys. No separate copy step; local dev mirrors prod.
- **Odoo version: prod (funedistri.odoo.com on Odoo.sh) = 19.2; local dev image `odoo:19` reports series 19.0** (verified at Step 0 scaffold, 2026-06-10). The community `odoo:19` image is the 19.0 generation — local does NOT mirror prod at the series level.
  - **Manifest version = short form `1.0.0`** (NOT `19.x.*`). A series-prefixed version that mismatches the running server makes Odoo set `installable=False` ("incompatible version"). The short form lets Odoo auto-prepend whichever series loads it, so the module installs on BOTH 19.0 (local) and 19.2 (prod). See `funedistri_customizations/__manifest__.py`.

## Coffin configurator = NATIVE ONLY (no custom config layer)
**RESOLVED 2026-06-15 (ADR 0004, reaffirmed):** coffin configuration is done **exclusively with native Odoo Product Attributes**. There is **no** custom config layer, **no** conditional reveal, **no** custom line fields. "Not perfect, but it does the job for v1." The earlier hybrid plan (custom date fields + a `coffin.config.rule` reveal model + reveal JS) is **dropped** — it was the most code, the most Odoo-upgrade risk, and the part that fought the framework hardest.

- **Priced / discrete options** (wood, handles, plaque type…) → native **product attributes & variants**.
  - Use **"no variant" mode** (don't auto-create SKU variants) → avoids combinatorial DB explosion; the selection is captured on the sale order line.
  - **Image dropdowns** → native "Image" display type on attribute values. ✅ native.
- **Free-text data** (engraving text, death date, delivery date) → native **`is_custom` attribute values** (`product.attribute.custom.value` on the line). Free text only — NO typed Date field, NO length limit, NO format validation. The Owner reads and corrects them at Validate.
- **Conditional reveal → OUT.** Native Odoo cannot show/hide a field based on another choice (it only has mutually-exclusive *exclusion* rules). We accept **always-visible fields**: e.g. a buyer can pick "no plaque" and still see/fill a plaque-name box. That contradiction is **not** prevented by the system — the **Owner is the single validation backstop** and fixes it at Validate (he fully edits every draft anyway, and the user base is small/curated).
- Output of checkout = a **draft sale order** (see Order workflow).
- **Backend visibility:** native `is_custom` values appear on the order line by default — no inherited view, no custom columns needed.
- All of this runs on the **website frontend** (`website_sale`), because B2B users never touch the backend.

> The dropped reveal layer (`coffin.config.rule`, custom line fields, reveal JS) was
> removed in the 2026-06-15 reset. The whole module is now an empty shell, rebuilt
> per `docs/IMPLEMENTATION_PLAN.md`; coffin config is native attributes only.

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
- Technical name = **`funedistri_customizations`** (folder name + manifest). Hard to rename later.

## Local dev setup (`make dev`)
- **Docker Compose**: official `odoo:19` image + `postgres:16` (Odoo 19 needs PG 14+). `docker compose up`.
- **`make dev`** = boot Postgres + Odoo, create a fresh DB, **auto-install the module + deps** (`website_sale`, `sale` via manifest `depends`), run in dev mode (`--dev=all`, hot-reload of XML/Python).
- **Repo layout**: the module dir(s) at the **repo root** (Odoo.sh treats each top-level dir with `__manifest__.py` as a module). Dev-only files (`Makefile`, `docker-compose.yml`, `odoo.conf`) sit alongside; Odoo.sh ignores anything without a manifest.
- **Local seed = the separate `funedistri_dev_seed` module** (NOT Odoo `demo` data; global demo stays off). `make dev` installs it alongside the main module; prod never does. After the 2026-06-15 reset it seeds only `seed_coffin_attributes.xml` (a configurable coffin); the test B2B companies/users return when step 2 re-adds `b2b_role`. See `funedistri_dev_seed/__manifest__.py`.

# Open questions
- Tracked in `docs/IMPLEMENTATION_PLAN.md` (step 6): **stock draw-down** (native BoM/MO vs custom — see `docs/explore-bom-mo.md`) and **orphan-user order visibility**. Each gets its own grilling session.
