# Implementation plan — fresh build (2026-06-15)

The module was reset to an empty, installable shell on 2026-06-15 (the previous
build accumulated too much scope, incl. a custom config layer dropped by ADR 0004).
We rebuild **step by step**, **tracer-bullet first**: get a thin end-to-end thread
working, then thicken it.

The target features are already decided — they live in the ADRs (`docs/adr/`) and
the glossary (`CONTEXT.md`). This plan is only the **order** in which we build them.

## Principles

- **One module, organised by feature** (ADR 0006). Each step adds its own files,
  grouped + commented per feature in `__manifest__.py`; keep `docs/FEATURE_MAP.md`
  current as steps land.
- **Native Odoo first** — coffin configuration is native Product Attributes only,
  no custom config layer, no conditional reveal (ADR 0004).
- **Server-side enforcement** for anything guarding money or integrity (price
  masking, address lock) — never client-only (ADR 0001, 0005).
- Each step ends **green**: module installs, `make dev` boots, the step's behaviour
  is clickable and (where it guards something) covered by a test.

## Steps

### Step 0 — Scaffold reset ✅ (done 2026-06-15)
Empty installable module (`depends: website_sale, sale, sale_management, contacts`;
empty `data`/`assets`). `make dev` boots, module installs, shop reachable. Seed
reduced to `seed_coffin_attributes.xml` only.

### Step 1 — Tracer spine ✅ (done 2026-06-15)
One **native** configurable coffin (product attributes, "no variant" mode) shows in
the shop. A custom **"Submit order"** button (no payment) creates a **Pending**
(`sale.order` draft) Order for the user's company, and notifies the Owner (a
`mail.activity` "To validate" + an email nudge). B2B user lands on a "pending
validation" page; the Order shows **Pending** in portal history.
- Fold the seed's real coffin (`seed_coffin_attributes.xml`) in so the tracer has
  something realistic to configure.
- ⚠️ Unguarded at this point — local only, do NOT push to prod until step 3.
- Refs: ADR 0004 (native config), CLAUDE.md order workflow.

### Step 2 — Roles foundation ✅ (done 2026-06-16)
Add the `b2b_role` Selection field (`salesman` / `store_owner`) on `res.partner`,
with a `write()`/`create()` sync to two hidden security groups
(`coffin_salesman_group` / `coffin_store_owner_group`). Dropdown on the contact
form. **Guardrail + test:** the sync toggles only the two coffin groups, never an
internal group — a B2B user stays portal after any role change.
- Restore `seed_b2b_users.xml` (two companies, both roles).
- Refs: ADR 0003 (role-sync guardrail).

### Step 3 — Login gate ✅ (done 2026-06-16)  → **prod-safe after this**
B2B users are native **portal** users (backend lockout is then structural, no
custom auth). Done with the native gate: `website.ecommerce_access='logged_in'`
makes website_sale's shop/product/cart/checkout controllers redirect the public
user to `/web/login` (the public landing stays anonymous). **No public
self-signup** via `auth_signup.invitation_scope='b2b'`. See `data/login_gate.xml`.
- Nuance vs ADR 0003's "coffins never published": native `is_published` is
  all-or-nothing (unpublishing would also blind logged-in B2B), so the gate
  closes the public door to the shop instead — same outcome; the seeded coffin
  stays published for B2B and is unreachable by the public.
- Refs: ADR 0003.

### Step 4 — Price masking ✅ (done 2026-06-16)
A **Salesman** sees **no price anywhere**, practical not adversary-proof (ADR 0001):
- **Render** (QWeb `groups=` → "Prix masqué" placeholder): shop grid, product page,
  cart line, cart/checkout totals, portal order list.
- **JSON routes** (server never emits the number): `/shop/cart/add|update` zeroed,
  `/shop/set_delivery_method` + `/shop/get_delivery_rate` placeholder'd.
- **Portal order detail + PDF/report**: BLOCKED for a Salesman (redirect to the
  order list) rather than masking ~15 fragile price nodes — v1 simplification; a
  masked detail page is a possible later refinement.
- **JS**: `coffin_checkout_mask.js` keeps the checkout Confirm button usable once
  the totals table is masked away.
- **Email**: N/A — flow A sends the Salesman no order email (only the Owner is
  notified), so there is nothing to mask.
- Interactive surfaces branch on the viewer's `has_group()`. The async/owner-context
  email+PDF branch-on-order-partner case from ADR 0001 isn't needed in flow A.
- Tests: `test_price_masking.py` (HttpCase). Run with `make test` (needs
  `--db-filter='.*'`; baked into the target).
- Refs: ADR 0001.

### Step 5 — Locked company address book ✅ (done 2026-06-16)
At checkout a B2B user may only **select** among their Customer company's
Owner-defined delivery addresses — no create, no edit, **server-enforced**:
`shop_address` (GET) + `shop_address/submit` (POST) refuse delivery for a B2B user,
`shop_update_address` validates the chosen delivery address is in the company's
allowed set, and `_check_cart_and_addresses` auto-assigns a company delivery
address so checkout shows the selection list (no redirect loop to the blocked
form). The delivery "Add Address" button is hidden (UX). Delivery only; invoice
native. Owner defines the addresses in the backend (child `type='delivery'`
contacts; they must be complete — name/email/phone/address — or native would
redirect to edit them).
- Refs: ADR 0005.

### Step 6 — Later (each its own grilling session)
- **Stock draw-down** — choosing a coffin Option value consumes the matching loose
  Part's stock; native (BoM/MO) vs custom. See `docs/explore-bom-mo.md`.
- ~~**Orphan-user order visibility**~~ ✅ RESOLVED 2026-06-16: native scoping already
  handles it — an orphan's `commercial_partner_id` is itself, so it sees no orders
  and never another company's. No code needed; locked by `test_order_visibility.py`.
  Orphan added to the dev seed (login `orphan`).

## Out of scope (v1)
Conditional reveal / custom config fields (ADR 0004); online payment; shipped-state
tracking; credit terms / order minimums; ORM-level price secrecy (ADR 0001).
