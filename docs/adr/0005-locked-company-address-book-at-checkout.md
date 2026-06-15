# 5. B2B checkout is locked to Owner-defined Company addresses (delivery)

Date: 2026-06-14

## Status

Accepted

## Context

The Owner negotiates shipping fees with each Customer company for a small, fixed
set of delivery addresses. If a B2B user could ship to an arbitrary new address,
the negotiated rate wouldn't apply — higher cost, lost margin. Per the Owner, that
is not acceptable.

Native `website_sale` checkout works against the customer's address book: it shows
the commercial partner's child *Delivery* contacts (good — already company-scoped)
**but also** offers "Add a new address" and lets the user **edit** addresses. There
is no native toggle to forbid creating/editing addresses at checkout. So the
defining requirement — "B2B users may only use addresses the Owner assigned" —
cannot be met by configuration alone.

As with price-masking (ADR 0001), hiding the add/edit UI client-side is not enough:
a crafted POST to the address route could still create or move an address. The
constraint protects real money (margin), so it must be enforced **server-side**.

## Decision

**At checkout, a B2B user may only *select* among their Customer company's
pre-defined delivery addresses. Creating and editing addresses is removed and
server-enforced. Scope = the delivery address only.**

- **Company address = native data.** The Owner creates each address as a child
  *Delivery* contact under the Customer company `res.partner`, in the backend. No
  custom model. They are already company-scoped at checkout.
- **No create, no edit at checkout.** The address step is overridden to hide
  "Add a new address" and the edit form, presenting a **select-only** list.
- **Server-enforced.** The address controller/route rejects any create or edit
  attempt for a B2B user (not just hides the UI), and validates the chosen
  delivery address belongs to the user's commercial partner's allowed set. A
  rogue address in a crafted request is refused.
- **Delivery only.** The lock covers the delivery address (the shipping-fee
  surface). The invoice/billing address keeps native behaviour / defaults to the
  company.
- **Owner-only management.** Addresses are added/changed solely by the Owner in the
  backend. A typo fix is the Owner's job, not the B2B user's.

## Consequences

- Negotiated shipping rates always apply: no order can ship to an unvetted address.
- Custom surface = one overridden checkout address step + a server guard, bounded
  and testable; we accept it because the rule guards margin, not convenience.
- A B2B user who needs a new ship-to must ask the Owner to add it — deliberate
  friction, acceptable for a small curated B2B base.
- Consistent with ADR 0001's guardrail: enforcement is server-side, never a
  client-only cover. A test should assert a crafted create/edit POST is rejected.
- New glossary term **Company address** (CONTEXT.md). Invoice-address behaviour is
  intentionally left native — revisit only if billing-address abuse appears.
