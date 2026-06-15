# 5. B2B checkout is locked to Owner-defined Company addresses (delivery)

Date: 2026-06-14 · Status: Accepted

## Decision

At checkout a B2B user may only **select** among their Customer company's pre-defined
delivery addresses. Creating and editing addresses is removed and **server-enforced**.
Scope = the **delivery** address only.

- **Company address = native data.** The Owner creates each as a child *Delivery*
  contact under the Customer company `res.partner`, in the backend. No custom model;
  already company-scoped at checkout.
- **No create, no edit at checkout.** The address step is overridden to a
  **select-only** list (hide "Add a new address" + the edit form).
- **Server-enforced.** The address route rejects any create/edit attempt by a B2B
  user and validates the chosen address belongs to the user's commercial partner's
  allowed set — a rogue address in a crafted request is refused (a test asserts this).
- **Delivery only.** Invoice/billing address keeps native behaviour.
- **Owner-only management.** A typo fix is the Owner's job, in the backend.

## Why

The Owner negotiates shipping fees per company for a small fixed set of addresses; a
B2B user shipping to an arbitrary new address breaks the negotiated rate (higher cost,
lost margin) — not acceptable. Native `website_sale` is already company-scoped but
offers "Add a new address"/edit with no toggle to forbid it, so configuration alone
can't meet the rule. As with ADR 0001, the constraint guards real money, so it must be
server-side, not a client-only UI hide. Deliberate friction (ask the Owner for a new
ship-to) is acceptable for a small curated B2B base.
