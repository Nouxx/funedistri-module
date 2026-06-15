# -*- coding: utf-8 -*-
# __manifest__.py is the ONE file Odoo looks for to recognise a folder as a
# module. It is a plain Python dict of metadata. Odoo.sh treats every top-level
# repo folder that contains this file as an installable module.
{
    # Human-readable name shown in the Apps list.
    "name": "Funedistri Coffin Configurator",
    # Version string. We use the SHORT form (no Odoo-series prefix) on purpose.
    # If you prefix the series and it mismatches the running server, Odoo marks
    # the module `installable=False` ("incompatible version"). Our local dev image
    # `odoo:19` reports series 19.0, while prod (funedistri.odoo.com on Odoo.sh) is
    # 19.2 — so any hard-coded series would break one of the two. With the short
    # form Odoo auto-prepends whatever series actually loads the module, so it
    # installs on BOTH. Three parts = module major.minor.patch, our own versioning.
    "version": "1.0.0",
    "summary": "Configurable B2B coffins with role-based price visibility.",
    "category": "Sales",
    "author": "Funedistri",
    "website": "https://funedistri.odoo.com",
    "license": "LGPL-3",
    # depends = other modules that MUST be installed first. Installing this module
    # auto-installs these. We build on Odoo's e-commerce (website_sale) which
    # itself pulls in sale. Listing sale explicitly documents that we use it
    # directly (sale.order / sale.order.line) and not only through website_sale.
    "depends": [
        "website_sale",     # the e-commerce frontend B2B users shop on
        "sale",             # sale.order / sale.order.line — the Order backbone
        "sale_management",  # the user-facing "Sales" BACKEND APP (menus, order
                            # views, settings). `sale` alone is the technical
                            # engine with no app menu; the Owner validates/edits
                            # Orders from this app, so depend on it explicitly —
                            # otherwise the Sales app is absent on a fresh DB.
        "contacts",         # Contacts app — where the Owner sets each B2B user's
                            # b2b_role on their res.partner (Step 2)
    ],
    # data = files (XML/CSV) loaded on install/update, in this order.
    "data": [
        # Step 2 roles: hidden security groups. Load FIRST — other records and
        # the field->group sync reference them by xmlid.
        "security/coffin_groups.xml",
        # Step 4: access rules for the coffin.config.rule model.
        "security/ir.model.access.csv",
        # Enable the "Variants" feature for backend users so the Attributes
        # menu is visible (replaces the demo seed's implicit enabling).
        "data/coffin_settings.xml",
        # Step 1 checkout overrides: Submit-order button + Pending confirmation.
        "views/checkout_templates.xml",
        # Step 1.5: portal list shows submitted Orders with a Pending badge.
        "views/portal_templates.xml",
        # Step 2.4: b2b_role dropdown on the contact form (backend).
        "views/res_partner_views.xml",
        # Step 4.7: surface per-line coffin config (engraving + dates) on the
        # backend sale order form so the Owner can see/edit what was captured.
        "views/sale_order_views.xml",
        # Step 4.5: per-line custom config fields on the cart page.
        "views/cart_templates.xml",
        # Step 6: Salesman price masking across shop/cart/checkout/portal list.
        "views/price_visibility_templates.xml",
    ],
    # Frontend JS/CSS bundles. web.assets_frontend loads on the website.
    "assets": {
        "web.assets_frontend": [
            # Step 4.6: generic conditional-reveal + save for the cart fields.
            "funedistri_coffin_configurator/static/src/js/coffin_cart_fields.js",
            # Step 6 fix: stop the native checkout JS from crashing (and leaving
            # the "Confirm" button disabled) when the Salesman's totals table is
            # masked away. See the file header for the full failure chain.
            "funedistri_coffin_configurator/static/src/js/coffin_checkout_mask.js",
        ],
    },
    # NO demo data. The old demo seed is retired; local dev test records (B2B
    # companies/users + a configurable coffin) now live in the separate, local-
    # only `funedistri_dev_seed` module, installed by `make dev` and never on
    # prod. Tests build their own fixtures (tests/common.py), so they don't rely
    # on any seed. See funedistri_dev_seed/__manifest__.py for the rationale.
    # application=False → this is a feature module, not a standalone "app" tile.
    "application": False,
    # installable=True → it shows up and can be installed.
    "installable": True,
}
