# 4. v1 captures all config data with native attributes; no conditional reveal

Date: 2026-06-14

## Status

Accepted (supersedes [ADR 0002](./0002-dedicated-model-for-conditional-reveal-rules.md))

## Context

Steps 3–4 built a hybrid configurator: native `product.attribute` for priced,
discrete choices (wood, handles), **plus** a custom layer for the rest — custom
`sale.order.line` fields (`engraving_text`, `death_date`, `delivery_date`), a
dedicated `coffin.config.rule` model for one-level conditional reveal (ADR 0002),
and a JS snippet that shows/hides cart fields from those rules.

Reassessing scope for v1 (new-context.md, 2026-06-14), the Owner wants **all**
per-line configuration data captured with native Odoo Product Attributes —
explicitly "not perfect but it will do the job for v1" — and is willing to drop
the conditional behaviour the custom layer existed to provide. The custom layer
is the most code, the most Odoo-upgrade risk, and the part that fights the
framework hardest (the cart-page JS, the rule model, the form-view columns).

The deciding facts:

- Native attributes support an `is_custom` value → a free-text box captured on the
  order line (`product_custom_attribute_value_ids`), shown natively on the backend
  order line. This covers engraving text and the dates **as free text**.
- Native attributes have **no conditional reveal** (only mutually-exclusive
  exclusion rules) — so going native means accepting always-visible fields.
- The Owner already fully edits every draft Order before Validating; he is a
  reliable backstop for the nonsense native can't prevent.

## Decision

For v1, **all per-line configuration data is native Product Attributes, and there
is no conditional reveal.** The entire custom config layer is removed.

- **Priced/discrete options** (wood, handles, plaque type) → native attributes
  with `price_extra`, exactly as today.
- **Engraving text** → a native `is_custom` text value. **No ≤20-char
  enforcement** — the Owner trims to fit the plate at Validate.
- **Death date / Delivery date** → native `is_custom` **free-text** values. No
  date picker, no validation, no typed field. The Owner reads and corrects them
  at Validate. (Death date is engraved, so a malformed date is the Owner's catch.)
- **Conditional reveal is dropped.** All fields are always visible. A Salesman can
  select "no plaque" and still type a plaque name; that contradiction is **not**
  prevented by the system — the Owner fixes it at Validate.
- **Removed:** `coffin.config.rule` (model, security, demo rules), the reveal JS
  (`coffin_cart_fields.js`), the custom `sale.order.line` fields and their
  `@api.constrains`, the cart custom-field template, and the custom columns added
  to the backend sale-order form for those fields.

## Consequences

- Far less code and near-zero custom surface for config data → much lower
  Odoo-upgrade risk, the stated v1 goal.
- The Owner becomes the **single validation backstop** for config-data integrity
  (date sanity, engraving length, plaque/name coherence). Acceptable because he
  already edits every draft before Validating, and the user base is small/curated.
- Lost vs. the hybrid: typed dates, length enforcement, and the plaque→name-
  required guarantee. Revisit post-v1 — ADR 0002 holds the design to revive.
- Glossary terms **Death date**, **Delivery date**, **Engraving text** now denote
  free-text option values, not typed/validated fields; **Reveal rule** is retired
  for v1. CONTEXT.md updated accordingly.
