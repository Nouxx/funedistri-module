# Feature map — `funedistri_coffin_configurator`

**One module, organised by feature.** We deliberately do **not** split features into
separate Odoo modules (single business, single Odoo.sh deploy, no reuse target —
see ADR 0006). Instead, Odoo's standard layer folders (`models/`, `views/`,
`controllers/`, …) hold **one file per feature** where practical, so each feature
reads as a whole instead of being scattered through grab-bag files named after
Odoo models.

This file is the map: **feature → the files that implement it.** Keep it current
when you add or move a feature. If a feature's logic *must* live inside a
shared-model file (e.g. an `inherit` on `res.partner` that several features touch),
note that here rather than letting the reader hunt for it.

## Naming convention

- A new self-contained feature → its own file in each layer it needs, named after
  the feature: `models/address_book.py`, `views/address_book_templates.xml`,
  `tests/test_address_book.py`.
- A feature that only *extends* an existing Odoo model can either get its own
  `models/<feature>.py` with a small `class ResPartner(models.Model): _inherit=...`,
  or fold into the shared file — pick whichever keeps the feature readable, and
  record the choice in the table below.
- `__manifest__.py` `data:` list stays grouped + commented per feature (already the
  habit) so load order is also a feature index.

## Features

| Feature | Models | Views | Controllers | Security / Data | JS/CSS | Tests | ADR |
|---|---|---|---|---|---|---|---|
| **B2B roles & group sync** (`b2b_role` → hidden groups) | `res_partner.py`, `res_users.py` | `res_partner_views.xml` | — | `coffin_groups.xml` | — | `test_b2b_role_sync.py` | 0003 |
| **Price masking** (Salesman sees no price) | `sale_order.py`, `website.py` | `price_visibility_templates.xml` | `main.py` (`CoffinWebsiteSale`, `CoffinCart`, `CoffinDelivery`, `_viewer_is_salesman`) | — | `coffin_checkout_mask.js` | `test_price_masking.py` | 0001 |
| **Submit-order flow** (Pending Order, owner notify, portal list) | `sale_order.py` | `checkout_templates.xml`, `portal_templates.xml` | `main.py` (`shop_submit_order`, `CoffinCustomerPortal`) | — | — | `test_submit_order.py` | — |
| **Configured-coffin config data** (wood, handles, engraving, dates) | — (native attributes only) | — | — | — | — | `test_catalog.py` | 0004 |
| **Catalog / variants settings** | — | — | — | `coffin_settings.xml` | — | `test_catalog.py` | — |

### Coffin config = native only (ADR 0004, reaffirmed 2026-06-15)

Coffin configuration is **exclusively native Product Attributes** — no custom config
layer, no conditional reveal, no custom line fields. Engraving text and the dates are
native `is_custom` free-text values.

**⚠️ Removal pending.** The dropped custom layer still sits in code and must be deleted
to execute ADR 0004:

- `models/coffin_config_rule.py` (whole model) + its `security/ir.model.access.csv` row
- custom fields + `_validate_reveal_rules` on `models/sale_order_line.py`
- `static/src/js/coffin_cart_fields.js`
- custom-field blocks in `views/cart_templates.xml` and the custom columns in `views/sale_order_views.xml`
- `main.py` reveal call (`coffin_save_line_field`, `_validate_reveal_rules()` at submit)
- `tests/test_reveal_rules.py`

Until removed, this code is **dead per the design** — do not build on it.

## Planned / not yet built

| Feature | Status | ADR |
|---|---|---|
| **Locked company address book** at checkout (B2B users pick from Owner-defined addresses only) | Designed, not coded | 0005 |
| **Stock draw-down** (choosing a coffin Option value consumes the matching loose Part's stock) | Open question (native vs custom) — see `docs/explore-bom-mo.md` | — |
| **Orphan-user order visibility** (user in no company sees no orders) | Open question | — |
