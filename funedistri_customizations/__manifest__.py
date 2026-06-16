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
    # Catch-all customizations module for Funedistri (one module, organised by
    # feature — ADR 0006). Named generically, not "coffin configurator", because it
    # holds ALL custom features (roles, price masking, address book, …), not just
    # the configurator.
    "name": "Funedistri Customizations",
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
    # data = XML/CSV loaded on install/update, in order. Grouped per feature.
    "data": [
        # --- Roles foundation (Step 2) ---
        # The two hidden security groups. Load FIRST: the b2b_role->group sync
        # resolves them by xmlid at runtime.
        "security/coffin_groups.xml",
        # b2b_role dropdown on the contact form.
        "views/res_partner_views.xml",
        # --- Login gate (Step 3) ---
        # Gate the shop to logged-in users + disable public self-signup.
        "data/login_gate.xml",
        # --- Submit-order flow (Step 1) ---
        # Owner-notification email template. Load before anything that references
        # it; the model looks it up by xmlid at submit time.
        "data/mail_template_owner_order.xml",
        # Submit button + Pending confirmation + portal status badge.
        "views/submit_order_templates.xml",
        # --- Price masking (Step 4) ---
        # Render-side "Prix masqué" placeholder across shop/cart/checkout/portal
        # list for the Salesman (JSON-route + portal-detail half is in Python).
        "views/price_visibility_templates.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            # Step 4: keep the checkout Confirm button usable when the totals
            # table is masked away for a Salesman (see the file header).
            "funedistri_customizations/static/src/js/coffin_checkout_mask.js",
        ],
    },
    # NO demo data. Local dev test records live in the separate, local-only
    # funedistri_dev_seed module (installed by `make dev`, never on prod).
    "application": False,
    "installable": True,
}
