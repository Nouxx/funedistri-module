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

> Reset 2026-06-15 — the module is an empty shell. This table fills in as steps
> land. Planned features and their order live in `docs/IMPLEMENTATION_PLAN.md`.

| Feature | Models | Views | Controllers | Security / Data | JS/CSS | Tests | ADR | Step |
|---|---|---|---|---|---|---|---|---|
| _(none yet — scaffold only)_ | — | — | — | — | — | — | 0006 | 0 |
