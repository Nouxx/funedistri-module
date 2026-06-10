# 1. Practical (not adversary-proof) price hiding for SALESMAN

Date: 2026-06-10

## Status

Accepted

## Context

A SALESMAN (a B2B customer role) must see **no price anywhere** — product page,
cart, checkout, confirmation email, portal order history, quote PDF. A
STORE_OWNER of the same company does see prices. The SALESMAN places orders on
behalf of their company while blind to price; the price materializes for the
owner / store owner when the owner validates the draft.

The original design (2026-06-07) called price-hiding a **real secret**: "must
not be fetchable via dev tools / raw requests… enforce in the ORM, not just
templates."

Native `website_sale` leaks price across a wide surface: QWeb templates, the
JSON cart/checkout routes (`/shop/cart`, `/shop/payment`, …), the `sale.order`
portal controller, mail templates, and the server-rendered quote PDF. Making
price a *true* secret means stripping it from every JSON route, overriding
`sale.order` / `sale.order.line` field-read access, neutering the mail
templates, and blocking the portal PDF — a large, fragile surface that fights
the framework on every Odoo upgrade.

The SALESMAN is a trusted B2B customer placing orders, **not** an adversary we
are defending against. The reason to hide price is operational (salesmen order
blind; pricing is the store owner's/owner's concern), not a security boundary
protecting a true secret.

## Decision

Hide price **practically, not adversary-proof**.

- Price is never **rendered** to a SALESMAN in normal use: product, cart,
  checkout, confirmation email, portal history, quote PDF.
- Masking is **server-side**: for a SALESMAN the server renders a placeholder
  (e.g. `XXXX €` / "Prix masqué", with a tooltip) and **never emits the real
  number** — not in the HTML, not in the JSON cart/checkout route responses.
- The role branch is a security **group** (`coffin_salesman_group` /
  `coffin_store_owner_group`), checked via `request.env.user.has_group(...)` in
  both QWeb and the overridden `website_sale` controllers — **for interactive
  requests where the current user IS the viewer**.
- For **server-side async renders** (confirmation email, quote PDF) the current
  user is NOT the salesman (system/owner context), so the branch keys off the
  **order partner's role**, not `env.user`. Concretely: the salesman
  confirmation email is a **bare** "order received" notice with no price/line
  table, and the portal quote PDF is **blocked** for salesmen rather than
  rendered price-free.
- We do **not** implement full ORM-level field-read security to stop a
  determined SALESMAN with dev tools from reconstructing a number.

## Consequences

- Much smaller, less fragile build: render-time + main-JSON-route suppression
  instead of ORM field-level security across every route.
- A `has_group()` check is the single, idiomatic hook for the price branch.
- **Guardrail:** masking must be server-side. A CSS/JS cover over a real number
  left in the DOM fails even this practical bar and is not acceptable.
- Residual risk accepted: a technical SALESMAN could in principle recover a
  price via crafted requests. Acceptable given the non-adversarial context.
- Door stays open: because the branch is a group, we can tighten toward strict
  ORM enforcement later without reworking the role model.
- Data integrity (e.g. required "death date" when engraving is chosen) is a
  **separate** concern and IS validated server-side — see the conditional-logic
  decision — because that protects order correctness, not price secrecy.
