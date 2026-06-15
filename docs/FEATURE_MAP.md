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
| **Submit-order flow** (cart → Pending Order, owner notify, portal status) | `sale_order.py` (`coffin_is_submitted`, `_coffin_submit_as_pending`, `_coffin_notify_owner`) | `submit_order_templates.xml` (button + confirmation + portal badge) | `submit_order.py` (`shop_submit_order`, portal domain) | `data/mail_template_owner_order.xml` | — | `test_submit_order.py` | — | 1 |

Dev seed (local only, in `funedistri_dev_seed`): `seed_coffin_attributes.xml` +
`seed_coffin_product.xml` give a published, configurable "Cercueil Taica" to build
and submit.
