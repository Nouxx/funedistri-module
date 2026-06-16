# Feature map — `funedistri_customizations`

**One module, organised by feature** (ADR 0006). We do not split features into
separate Odoo modules. Inside the single module, Odoo's standard layer folders
(`models/`, `views/`, `controllers/`, `security/`, `data/`) hold **one file per
feature** where practical, so each feature reads as a whole instead of scattering
through grab-bag files named after Odoo models.

This file is the map: **feature → the files that implement it.** Keep it current as
steps land (see `docs/IMPLEMENTATION_PLAN.md`).

## Naming convention

- A new self-contained feature → its own file in each layer it needs, named after
  the feature: `models/address_book.py`, `views/address_book_templates.xml`,
  `tests/test_address_book.py`.
- A feature that only *extends* an existing Odoo model can get its own
  `models/<feature>.py` (small `_inherit` class) or fold into a shared file — pick
  whichever keeps the feature readable, and record the choice in the table below.
- `__manifest__.py` `data:` list stays grouped + commented per feature so load
  order is also a feature index.

## Features

> This table fills in as steps land. Planned features and their order live in
> `docs/IMPLEMENTATION_PLAN.md`.

| Feature | Models | Views | Controllers | Security / Data | JS/CSS | Tests | ADR | Step |
|---|---|---|---|---|---|---|---|---|
| **Submit-order flow** (cart → Pending Order, owner notify, portal status, cart cleared after submit) | `sale_order.py` (`coffin_is_submitted`, `_coffin_submit_as_pending`, `_coffin_notify_owner`); `website.py` (`_get_and_cache_current_cart` drops submitted Orders) | `submit_order_templates.xml` (button + confirmation + portal badge) | `submit_order.py` (`shop_submit_order`, portal domain) | `data/mail_template_owner_order.xml` | — | `test_submit_order.py` | — | 1 |
| **B2B roles** (`b2b_role` → hidden groups; portal-stays-portal guardrail) | `res_partner.py` (`b2b_role`, `_sync_b2b_role_to_users`); `res_users.py` (`create` sync) | `res_partner_views.xml` (role dropdown) | — | `security/coffin_groups.xml` (2 hidden groups) | — | `test_b2b_role_sync.py` | 0003 | 2 |
| **Order visibility** (company-scoped, orphan sees none) | — (native `commercial_partner_id` scoping) | — | — | — | — | `test_order_visibility.py` | 0003 | 2 |
| **Login gate** (shop gated to logged-in; no public signup; portal = backend lockout) | — (native `website.ecommerce_access`) | — | — | `data/login_gate.xml` (`ecommerce_access='logged_in'` + `auth_signup.invitation_scope='b2b'`) | — | `test_login_gate.py` | 0003 | 3 |
| **Shop access** (only configured B2B users/staff shop; orphan → /my, no loop) | `res_users.py` (`_coffin_can_shop`) | — | `shop_access.py` (guards `shop`/`product`/`cart`) | — | — | `test_shop_access.py` | 0003 | 3 |

Dev seed (local only, in `funedistri_dev_seed`): `seed_coffin_attributes.xml` +
`seed_coffin_product.xml` give a published, configurable "Cercueil Taica" to build
and submit.
