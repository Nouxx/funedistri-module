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
