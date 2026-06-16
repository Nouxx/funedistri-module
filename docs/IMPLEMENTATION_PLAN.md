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

### Step 3 — Login gate  → **prod-safe after this**
B2B users are native **portal** users (backend lockout is then structural, no
custom auth). Two-layer gate on the configurator: (data) coffins are **never
published** to the public website; (auth) shop/cart/checkout/portal routes force
login. **No public self-signup.** Public landing stays anonymous.
- Refs: ADR 0003.

### Step 4 — Price masking
A **Salesman** sees **no price anywhere**: product, cart, checkout, portal history
(render + the JSON cart/checkout routes), a **bare** confirmation email, and a
**blocked** quote PDF. Server-rendered placeholder ("Prix masqué") + tooltip; branch
on `has_group()` for interactive requests, on the **order partner's role** for async
renders (email/PDF). Practical, not adversary-proof.
- Refs: ADR 0001.

### Step 5 — Locked company address book
At checkout a B2B user may only **select** among their Customer company's
Owner-defined delivery addresses — no create, no edit, **server-enforced** (a
crafted POST is rejected). Delivery address only; invoice stays native. Owner
manages addresses in the backend.
- Refs: ADR 0005.

### Step 6 — Later (each its own grilling session)
- **Stock draw-down** — choosing a coffin Option value consumes the matching loose
  Part's stock; native (BoM/MO) vs custom. See `docs/explore-bom-mo.md`.
- **Orphan-user order visibility** — a user in no company should see no orders.

## Out of scope (v1)
Conditional reveal / custom config fields (ADR 0004); online payment; shipped-state
tracking; credit terms / order minimums; ORM-level price secrecy (ADR 0001).
