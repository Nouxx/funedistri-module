# -*- coding: utf-8 -*-
# __manifest__.py is the ONE file Odoo looks for to recognise a folder as a
# module. It is a plain Python dict of metadata. Odoo.sh treats every top-level
# repo folder that contains this file as an installable module.
#
# FRESH START (2026-06-15): the module was reset to an empty, installable shell.
# Features are rebuilt step by step per docs/IMPLEMENTATION_PLAN.md. Each step
# adds its own files to `data` / `assets` below, grouped + commented per feature
# (see docs/FEATURE_MAP.md and ADR 0006 — one module, organised by feature).
{
    "name": "Funedistri Coffin Configurator",
    # SHORT version form (no Odoo-series prefix) on purpose: a series prefix that
    # mismatches the running server marks the module installable=False. Local dev
    # image odoo:19 reports series 19.0, prod (Odoo.sh) is 19.2 — the short form
    # lets Odoo auto-prepend whichever series loads it, so it installs on BOTH.
    "version": "1.0.0",
    "summary": "Configurable B2B coffins with role-based price visibility.",
    "category": "Sales",
    "author": "Funedistri",
    "website": "https://funedistri.odoo.com",
    "license": "LGPL-3",
    # depends = modules installed before this one. We build on Odoo e-commerce.
    "depends": [
        "website_sale",     # the e-commerce frontend B2B users shop on
        "sale",             # sale.order / sale.order.line — the Order backbone
        "sale_management",  # the user-facing "Sales" BACKEND APP (menus/views)
        "contacts",         # Contacts app — where the Owner sets b2b_role (step 2)
    ],
    # data/assets are EMPTY at the reset. Steps fill them in as features land.
    "data": [],
    "assets": {},
    # NO demo data. Local dev test records live in the separate, local-only
    # funedistri_dev_seed module (installed by `make dev`, never on prod).
    "application": False,
    "installable": True,
}
