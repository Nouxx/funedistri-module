# 5. B2B checkout is locked to Owner-defined Company addresses

Date: 2026-06-14 · Status: Accepted (scope extended 2026-06-16)

## Decision

A B2B user (Salesman **or** Store owner) may **never create or edit any address** —
at checkout or in the portal. Only the **Owner** manages addresses (backend). At
checkout a B2B user may only **select** among their Customer company's pre-defined
addresses, with a strict separation by contact type. Server-enforced (guards
negotiated-shipping margin and billing correctness), not just a UI hide.

- **Company address = native data.** The Owner creates child contacts under the
  Customer company `res.partner`: *Delivery*-type for shipping, *Invoice*-type for
  billing. No custom model.
- **Shipping** is selectable **only** from the company's *Delivery* contacts;
  **billing** **only** from its *Invoice* contacts. The two never cross — an invoice
  address can't be shipped to and a delivery address can't be billed to. To use one
  physical location for both, the Owner creates **two records** (one of each type);
  **no auto-mirror**.
- **No create/edit anywhere.** Both the checkout address step and the portal address
  book are select-only for a B2B user (add/edit removed + server-refused). The user
  may still edit their own **login profile** (name/email/password), but their own
  contact is neither Delivery nor Invoice type, so it is **never selectable** as an
  order address.
- **Auto-assign + hard stop.** Checkout auto-assigns the company's first address of
  each type so the selection list shows (no redirect loop to a blocked form). If the
  company lacks a Delivery **or** an Invoice address, checkout is **blocked** until
  the Owner defines it (no fallback to the user's own address).
- **Server-enforced.** The address routes reject any create/edit by a B2B user and
  validate the chosen address is in the company's allowed set **of the right type** —
  a rogue or wrong-type id in a crafted request is refused.

## Why

The Owner negotiates shipping per company for a small fixed set of addresses, and
billing must land on a known company invoice entity; a B2B user shipping or billing to
an arbitrary/edited address breaks the negotiated rate or the billing record — not
acceptable. Native `website_sale` is company-scoped but offers add/edit with no toggle
to forbid it and lets any child contact (any type) serve as either address — too
loose. As with ADR 0001, the constraint guards real money, so it is server-side, not a
client-only hide. Deliberate friction (ask the Owner for a new address) is acceptable
for a small curated B2B base. The two-records-per-location quirk is accepted as the
price of the hard type separation.

## Note (2026-06-16)

This extends the original (delivery-only, invoice native) scope to **both** address
types + the **portal** surface + the **strict type separation** + **block-on-missing**.
**Built** (Step 5 = delivery half; Step 5b = invoice lock + portal lock + type
separation + block-on-missing). The glossary term **Company address** (CONTEXT.md) now
covers both **Company delivery address** and **Company invoice address**.
