# 2. Dedicated model for conditional-reveal rules

Date: 2026-06-10

## Status

Accepted

## Context

A Coffin model needs **one-level conditional reveal**: picking option X
reveals / requires field Y (e.g. choosing engraving = yes reveals the death-date
field, and makes it required). The rules must be a **single source of truth** in
Python/data: the product page renders them into the DOM for a small JS snippet
(show/hide/disable — UX only), and the **server reads the same rules** to validate
required-when fields. No rule may be duplicated in JS.

The open question was *where the rules physically live*. CLAUDE.md left it as
"e.g. on the attribute value / a config record." Two candidates:

- **(a) Fields on native `product.attribute.value`** — add columns like
  `reveals_field`. No new model; the rule sits on the value that triggers it.
- **(b) A dedicated custom model** `coffin.config.rule` — rows of
  `(trigger, target_field, required_when)`.

The deciding constraint: **a trigger is not always a priced attribute value.**
"Engraving = yes" is a custom yes/no field, not a `product.attribute.value`.
Option (a) can only attach a rule when the trigger happens to be a native value;
the moment a custom field is the trigger it has nowhere to live, and rule
fragments scatter across native records.

## Decision

Store conditional-reveal rules in a **dedicated model** `coffin.config.rule`.

- Each row is `(trigger, target_field, required_when)`.
- `target_field` is a Selection over the **dev-defined custom fields** on
  `sale.order.line` (`death_date`, `delivery_date`, `engraving_text`, …) —
  consistent with the "fields live in code, stored on the line" decision.
- The trigger is represented uniformly regardless of type (native attribute value
  *or* custom yes/no field).
- The product page renders these rows into DOM `data-*` attributes; the JS reads
  them; the server reads the **same** rows to validate. One table, three readers,
  zero duplication.

## Consequences

- One queryable source of truth: server validation and page rendering read the
  same rows, satisfying the "no rule duplicated in JS" guardrail.
- Works uniformly for every trigger type — priced dropdown *or* custom field —
  which option (a) could not.
- Cost: one more custom model to maintain, versus reusing native records. Accepted
  — it keeps the custom layer's rules coherent and is the thing the server trusts.
- Adding a brand-new custom *field* is still a dev touch (a new column + a new
  Selection entry); wiring an existing field to a trigger is data-only, no rewrite
  per rule — matching the "generic mechanism, thin custom layer" goal.

## Update — Step 4 implementation (2026-06-13)

Two refinements made while building the layer; the core decision (dedicated model,
one source of truth, server validates) stands.

1. **The trigger is a native attribute value, not a custom yes/no field.** This
   ADR's motivating example imagined "engraving = yes" as a custom Boolean. In
   practice we model engraving as a native **Gravure (Oui/Non)** attribute (like
   Bois/Poignées), so the trigger is a `product.attribute.value` —
   `coffin.config.rule.trigger_value_id`. Benefits: reuses the Step 3 attribute
   machinery, stays Owner self-serve (Attributes & Variants tab), and needs no new
   field-type/widget. The rule keys on the **global** value (not the per-coffin
   PTAV) so it applies wherever that value is offered; a line is matched by mapping
   its selected PTAVs back to their global values. (`target_field` is still a
   Selection over custom `sale.order.line` fields, as decided.) The "generic
   trigger that also covers non-native fields" remains possible later, but is not
   built — current triggers are native values only.

2. **Capture is on the cart page, not the product page.** The ADR said the product
   page renders the rules. In Odoo 19 the product page is an OWL/JS configurator;
   injecting custom inputs that feed its add-to-cart JSON is fragile and
   version-sensitive. The **cart page** (`cart_lines`, server-rendered QWeb) is
   robust to extend and the line already exists there. So the optional fields are
   rendered per line on the cart, the rules go into DOM `data-*`, and a small
   generic JS shows/hides them — **no rule duplicated in JS**, unchanged. Trade-off:
   reveal is per-line (the option is already chosen) rather than live-toggling on
   the product page. The server still validates required-when at submit
   (`/shop/submit_order` → `sale.order.line._validate_reveal_rules`), and the
   ≤20-char engraving limit is an `@api.constrains` enforced on every write.
