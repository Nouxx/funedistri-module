# 7. Stock-consuming options become real (dynamic) variants for native draw-down

Date: 2026-06-17 · Status: Accepted (one sub-decision open: Kit vs MO)

Amends ADR 0004 (which made **all** coffin options no-variant). See its cross-ref note.

## Context

A **Part** (handle, plate, urne…) is a physical component the Owner both **sells
loose** and **consumes inside a coffin**, off **one shared stock**. Choosing the
matching Option value on a coffin must draw down that shared Part stock so loose
sales and coffin sales can't oversell it. In this domain, **every stock-consuming
Option is already a standalone, independently-sold product** — the attribute on the
coffin is only UX sugar over that product.

Native Odoo stock draw-down (Kit BoM, or normal BoM + Manufacturing Order — see
`docs/explore-bom-mo.md`) maps an option choice to a component via the BoM
**"Apply on Variants"** column, which keys off a **real `product.product` variant**.
ADR 0004 made every coffin option **no-variant** (config captured on the order line,
zero variant rows) — and no-variant values **cannot** drive "Apply on Variants".
So the two decisions collide: native draw-down needs variants; 0004 forbade them.

## Decision

For the **stock-consuming options only**, take the native-BoM path and accept real
variants:

- **Stock-consuming options → real variants, mode "Dynamically".** A
  `product.product` is created only when a combination is actually ordered — no idle
  pre-created matrix (e.g. plate 3 × handles 5 × urne 3 × wood 4 = 180 stays virtual).
  "Apply on Variants" still applies to dynamically-created variants.
- **Mixed model.** Only stock options become variants. Free-text / informational
  options (engraving text, death date, delivery date) **stay no-variant /
  `is_custom`** per ADR 0004. Odoo allows both modes on one template.
- **Value→Part mapping = native** BoM component lines + "Apply on Variants" (oak-handle
  component line → applies to value *Oak*). One BoM per Coffin model, ~one line per
  value. No custom link field.
- **Trigger.** On the Owner's **Validate** (`action_confirm`), Odoo creates the
  delivery and **reserves** the components — that reservation is the oversell
  protection, at the right moment. The actual stock **decrement** happens at the
  Owner's later, informal **delivery validation** — consistent with "Shipped is out
  of scope".
- **Oversell while Pending = Owner backstop.** Pending (draft) reserves nothing by
  design. If several companies submit for the last Part, the first Validate reserves
  it and later ones get the native stock warning; the Owner reorders/contacts. No code.
- **No double-counting.** Under Kit/MO the Part components carry **cost**, not a
  customer-facing line price; the coffin's price stays on its variant `price_extra`.
  (Side effect: the Owner enters each Part's price twice — coffin `price_extra` plus
  the standalone product's list price — they can diverge; data hygiene, not a bug.)

### Open sub-decision — Kit BoM vs normal BoM + MO

Both shortlisted, not yet picked:

1. **Kit BoM** — coffin is phantom; on delivery it explodes into the chosen Part
   products; **zero extra paperwork**; coffin not tracked as finished-good stock.
2. **Normal BoM + MO** — one Manufacturing Order per coffin the Owner opens/closes to
   consume parts; coffin becomes its own +1 finished-good stock; more control + paperwork.

Everything above holds either way; this fork only changes the build/explode mechanics.

## Why

The custom alternative — keep the coffin fully no-variant and decrement the linked
Part with a hand-written stock move at `action_confirm` — was weighed and rejected:
it reimplements reservation/decrement the framework already does, and the Owner
already runs Odoo Stock + Manufacturing. Going native means living with variants for
the stock options, but **"Dynamically"** contains the explosion ADR 0004 feared
(virtual until ordered, small curated B2B base), and the rest of the configurator
keeps 0004's no-variant model. Reserve-at-Validate / decrement-at-delivery matches
the existing Pending → Validate → (informal) Shipped flow without building a delivery
feature.

## Consequences

- The seeded coffin and its stock options are no-variant today; this step converts
  the stock options to dynamic variants — touches `seed_coffin_attributes.xml` and may
  ripple into `test_price_masking` / `test_address_lock` fixtures.
- Build order and remaining detail live in `docs/IMPLEMENTATION_PLAN.md` step 6.
