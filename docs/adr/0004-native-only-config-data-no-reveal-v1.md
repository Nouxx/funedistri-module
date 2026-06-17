# 4. v1 captures all config data with native attributes; no conditional reveal

Date: 2026-06-14 · Status: Accepted, reaffirmed 2026-06-15 · **Amended by ADR 0007**

> **Amendment (ADR 0007, 2026-06-17):** "all options no-variant" is narrowed.
> **Stock-consuming** options (Parts sold loose + consumed in a coffin) become real
> **dynamic** variants so native BoM draw-down can key off them; free-text /
> informational options below stay no-variant / `is_custom` as written here.

## Decision

For v1, **all per-line coffin configuration data is native Product Attributes, and
there is no conditional reveal.** No custom config layer.

- **Priced/discrete options** (wood, handles, plaque type) → native attributes with
  `price_extra`.
- **Engraving text, Death date, Delivery date** → native `is_custom` **free-text**
  values (`product_custom_attribute_value_ids`, shown natively on the backend order
  line). No typed Date field, no length limit, no format validation.
- **Conditional reveal is dropped.** All fields are always visible — a buyer can pick
  "no plaque" and still type a plaque name; that contradiction is **not** prevented.
  The **Owner is the single validation backstop** and fixes it at Validate.

## Why

The Owner wants config data captured natively — "not perfect but it does the job for
v1" — and will drop the conditional behaviour. The custom layer (a `coffin.config.rule`
model + reveal JS + custom line fields) was the most code, the most Odoo-upgrade risk,
and the part that fought the framework hardest. Native covers the data as free text;
native has **no** conditional reveal (only mutually-exclusive exclusion rules), so
going native means accepting always-visible fields. Acceptable because the Owner
already fully edits every draft before Validating, and the user base is small/curated.

## Reaffirmation (2026-06-15)

After this was accepted, conditional reveal was re-opened (the "plaque chosen → plaque
name must be provided" example) on the grounds that always-visible fields are
nonsensical UX. **Rejected** — native attributes only, no reveal, full stop for v1.

Revival note (post-v1): the dropped design was a dedicated `coffin.config.rule` model
+ reveal JS over **custom** `sale.order.line` fields. The re-open instead wanted reveal
over **native** attribute data. Native `is_custom` values already give "same-value
reveal" for free (pick an `is_custom` value → its text box appears), but never
*required* and never *cross-attribute* (e.g. engraving=yes → a separate death-date
field). Those two gaps are the only things a custom layer buys — weigh them against the
upgrade-risk cost before reviving.
