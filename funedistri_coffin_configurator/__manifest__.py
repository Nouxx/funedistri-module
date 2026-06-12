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
        "website_sale",  # the e-commerce frontend B2B users shop on
        "sale",          # sale.order / sale.order.line — the Order backbone
        "contacts",      # Contacts app — where the Owner sets each B2B user's
                         # b2b_role on their res.partner (Step 2)
    ],
    # data = files (XML/CSV) loaded on install/update, in this order.
    "data": [
        # Step 2 roles: hidden security groups. Load FIRST — other records and
        # the field->group sync reference them by xmlid.
        "security/coffin_groups.xml",
        # Step 1 tracer: one hardcoded, published, sellable coffin so we can
        # prove the shop -> cart -> submit -> draft Order pipe end to end.
        "data/tracer_coffin.xml",
        # Step 1 checkout overrides: Submit-order button + Pending confirmation.
        "views/checkout_templates.xml",
        # Step 1.5: portal list shows submitted Orders with a Pending badge.
        "views/portal_templates.xml",
        # Step 2.4: b2b_role dropdown on the contact form (backend).
        "views/res_partner_views.xml",
    ],
    # demo = data loaded ONLY when the DB is created with demo enabled (our dev
    # DB). Never loads in production. The demo company + portal users + sample
    # coffin land here in Step 3.
    "demo": [],
    # application=False → this is a feature module, not a standalone "app" tile.
    "application": False,
    # installable=True → it shows up and can be installed.
    "installable": True,
}
