# 1. Practical (not adversary-proof) price hiding for SALESMAN

Date: 2026-06-10 · Status: Accepted

## Decision

A **Salesman** must see **no price anywhere** (product, cart, checkout, portal
history, confirmation email, quote PDF); a **Store owner** of the same company does.
We hide price **practically, not adversary-proof**:

- Price is never **rendered** to a Salesman, and **never emitted** in the JSON
  cart/checkout route responses — server renders a placeholder ("Prix masqué" +
  tooltip) instead. **Masking must be server-side**: a CSS/JS cover over a real
  number left in the DOM fails even this bar and is not acceptable.
- The role branch is a security **group** (`coffin_salesman_group` /
  `coffin_store_owner_group`), checked via `request.env.user.has_group(...)` for
  **interactive** requests (current user = viewer).
- For **async renders** (confirmation email, quote PDF) the current user is NOT the
  salesman (system/owner context), so branch on the **order partner's role**, not
  `env.user`: the salesman confirmation email is a **bare** "order received" notice
  (no price/line table), and the portal quote PDF is **blocked** for salesmen.
- We do **not** build ORM-level field-read security.

## Why

The Salesman is a trusted B2B customer ordering blind (pricing is the owner's/store
owner's concern), **not** an adversary. Making price a true secret means stripping
it from every JSON route + overriding field-read access + neutering mail templates
+ blocking the PDF — a large, fragile surface that fights the framework on every
upgrade. Render-time + main-JSON-route suppression is far smaller and the group
check is a single idiomatic hook. Residual risk (a technical salesman reconstructing
a number via crafted requests) is accepted. Because the branch is a group, we can
tighten toward strict ORM enforcement later without reworking the role model. Data
integrity (e.g. a required field) is a **separate** concern, validated server-side.
