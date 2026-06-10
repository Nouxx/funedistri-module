# Implementation plan — Funedistri coffin configurator

Step-by-step build order for the `funedistri_coffin_configurator` Odoo 19.2 module.
Resolved in the grilling session of 2026-06-10. Read alongside `CLAUDE.md`
(design decisions), `CONTEXT.md` (language) and `docs/adr/`.

## Shape of the plan (the decisions behind the order)

- **Tracer-bullet first, then layer** (grilling Q1 = A). Build a thin end-to-end
  spine that proves the whole pipe — shop → cart → submit → draft order — then
  bolt features onto a spine you already trust. Rationale: fastest path to "I can
  click it" derisks the Odoo unknowns; the fragile parts (roles, masking) are
  additive `has_group()` branches, cheap to retrofit.
- **Masking is a dedicated late pass, not as-you-go** (Q2 = ii). The guarantee is
  "no price *anywhere*" — that is an audit against the *complete* surface. One
  sweep when every surface exists = one coherent check; piecemeal you cannot tell
  which surface you missed. Roles still land early so you can log in as both users
  to verify the sweep.
- **Conditional-reveal rules live in a dedicated model** `coffin.config.rule`
  (Q3 = b → ADR-0002), not scattered on native attribute values — because a
  trigger is not always a priced attribute value (e.g. "engraving = yes" is a
  custom yes/no field).
- **Verification = hybrid** (Q4 = c). Automated tests for the *server-truth
  invariants* (≤20-char constraint, role↔group sync, JSON-route price-strip,
  required-when validation); manual click-through for QWeb visuals + JS reveal.
  "Test the truth, eyeball the UX."

Each step below is **one shippable commit** with an explicit *Done when*. Do them
in order; do not start a step until the previous one's *Done when* holds.

---

## Step 0 — Scaffold & boot

**Goal:** `make dev` boots Odoo 19.2 with an empty module installed.

Build:
- Repo-root module dir `funedistri_coffin_configurator/` with `__init__.py` and
  `__manifest__.py` (version `19.2.1.0.0`, `depends = ['website_sale', 'sale']`).
- Dev-only files alongside (Odoo.sh ignores anything without a manifest):
  `docker-compose.yml` (`odoo:19` + `postgres:16`), `odoo.conf`, `Makefile`.
- `make dev` = boot PG + Odoo, create fresh DB, auto-install module + deps,
  run `--dev=all` (hot-reload).

**Done when:** `make dev` boots clean, module installs with no error, Odoo login
reachable. *(manual)*

---

## Step 1 — Tracer spine

**Goal:** prove the full pipe with ONE hardcoded coffin. No roles, no prices, no
conditional fields, no notifications yet.

Build:
- One hardcoded coffin `product.template` (data XML), published + sellable on the
  website.
- Override the `website_sale` checkout final step → **"Submit order"** (flow A,
  no online payment) that creates a `sale.order` in **draft** state assigned to
  the user's company.
- Confirmation page: "Order received — en attente de validation". Order shows
  **Pending** in portal history (never "quotation", never "paid").

**Done when:**
- *(manual)* as a plain portal user: add coffin → submit → draft `sale.order`
  appears in backend; portal shows Pending.
- *(test)* controller creates the order in `state = 'draft'`.

---

## Step 2 — Roles foundation

**Goal:** the role model that every later price branch hooks into.

Build:
- `b2b_role` Selection field (`salesman` / `store_owner`) on `res.partner`.
- Two `res.groups`: `coffin_salesman_group`, `coffin_store_owner_group`.
- `write()` override on `res.partner` syncing `b2b_role` → the matching hidden
  group (field-drives-group; the owner edits one dropdown).

**Done when:**
- *(test)* setting `b2b_role` writes the correct group; changing it re-syncs;
  clearing it removes the group.
- *(manual)* owner sees the dropdown on the contact in the backend.

---

## Step 3 — Catalog & demo seed

**Goal:** replace the hardcoded coffin with a real **Coffin model** built from
native attributes; give every `make dev` a clickable store.

Build:
- Native `product.attribute` + `product.attribute.value` with `price_extra`,
  **"no variant"** mode, "Image" display type for image dropdowns.
- Demo data (dev DB only, never prod): 1 customer company (`res.partner` parent)
  + 1 Store owner + 1 Salesman portal user, all sharing one
  `commercial_partner_id`; + 1 configurable coffin with a few priced / image /
  text options.

**Done when:**
- *(manual)* logged in as the Store owner, build the coffin picking options;
  `price_extra` reflected in the line price.
- *(test)* the two demo B2B users share `commercial_partner_id` (native
  company-scoped order visibility holds).

---

## Step 4 — Conditional layer  *(see ADR-0002)*

**Goal:** one-level conditional reveal + the server-side data-integrity rules.

Build:
- `coffin.config.rule` model: `(trigger, target_field, required_when)`.
  `target_field` = a Selection over the dev-defined custom fields.
- Custom **optional** fields on `sale.order.line`: `death_date`, `delivery_date`,
  `engraving_text` (dev adds new ones in code; each optional).
- Product page renders the rules into DOM `data-*` attributes; a small custom JS
  snippet consumes them to show / hide / disable fields. **No rule duplicated in
  JS.**
- Server reads the **same** rules to validate (`@api.constrains` / controller):
  required-when fields, plus the ≤20-char `engraving_text` constraint.

**Done when:**
- *(test)* required-when fails when the trigger is set and the target is empty;
  ≤20-char rejects a 21-char engraving.
- *(manual)* pick engraving = yes → death-date field reveals; JS hide/disable
  works.

---

## Step 5 — Owner notification on submit

**Goal:** no submitted order sits unseen.

Build (in the Submit-order controller, on draft creation):
- `activity_schedule()` "To validate" on the new `sale.order`, assigned to the
  owner — the durable native to-do (primary guarantee).
- Mail template **nudge** to the owner to come look.

**Done when:**
- *(test)* submit schedules the activity on the order for the owner.
- *(manual)* owner sees the activity + receives the email.

---

## Step 6 — Masking pass + "no price anywhere" audit

**Goal:** the dedicated masking sweep across every interactive surface for the
Salesman. *(See ADR-0001.)*

Build:
- QWeb `has_group()` swaps price → placeholder ("Prix masqué" / `XXXX €`) + a
  tooltip explaining why, across product page, cart, checkout, portal history.
- Override the `website_sale` JSON cart/checkout routes to strip / zero amounts
  for a Salesman — the server **never emits the real number**.

**Done when:**
- *(test = the audit)* as a Salesman, assert no real price in any JSON route
  response (cart / checkout) and none in the rendered HTML.
- *(manual)* every surface as Salesman shows no number; as Store owner the numbers
  are present.

---

## Step 7 — Email & PDF price suppression  *(keyed off partner role)*

**Goal:** close the async-render surfaces, which run in owner/system context
(so branch on the **order partner's** `b2b_role`, not `env.user`).

Build:
- Salesman confirmation email = **bare** "order received — pending validation",
  no line/price table at all.
- **Block** the portal quote PDF route for a Salesman (access check), rather than
  rendering a price-free report.

**Done when:**
- *(test)* the email render for a Salesman-partner order contains no price; the
  PDF route returns forbidden/redirect for a Salesman.
- *(manual)* confirmed as a Salesman.

---

## Out of scope for now
- **Shipped** as a real `sale.order` state (needs `stock`/delivery) — informal,
  owner-tracked.
- Credit terms, order minimums, approval rules.
- A meta-configurator UI for the owner to invent new field *types* (new field
  type = a dev touch; these change rarely).
- Adversary-proof price hiding (ADR-0001: practical, not adversary-proof).

## Pre-flight (Open question 1, before Step 1 writes any model code)
- Odoo version confirmed 19.2. Still re-check `sale.order.state` at scaffold —
  the enum changed in v17 (old `done` removed) — before relying on it.
