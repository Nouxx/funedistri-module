# Single module, organised by feature (no per-feature modules)

All Funedistri features (price masking, B2B roles, submit-order flow, configured-coffin
line data, conditional reveal, and the planned address book + stock draw-down) live in
**one** Odoo module, `funedistri_coffin_configurator`. We will not split features into
separate modules.

## Context / trade-off

An Odoo module split pays off for exactly two reasons: (1) **independent reuse** —
another DB/client installs feature X without Y; (2) **independent install/uninstall
lifecycle**. Funedistri is a single business with a single Odoo.sh deploy and no
reuse target, and every feature hangs off the same `b2b_role` and the same checkout
flow — they are tightly coupled, not independently useful. Splitting would add N
manifests, N dependency edges, N test suites, and cross-module xmlid references for
zero payoff. The separation we actually want (readability, testability) is bought by
**folders + one-file-per-feature inside the single module**, documented in
`docs/FEATURE_MAP.md`, not by separate modules.

`funedistri_dev_seed` stays a separate module — it is local-only test data with a
genuinely different lifecycle (never installed on prod).

## When to revisit

Split a feature out only if it gains a real **reuse target** (e.g. a generic "B2B
price masking" addon for another site) or a **heavy optional dependency** we don't
always want loaded (e.g. Manufacturing/`mrp` for stock draw-down on a website-only
deploy).
