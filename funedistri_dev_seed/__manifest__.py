# -*- coding: utf-8 -*-
# =====================================================================
#  LOCAL DEV SEED — NEVER INSTALL ON PRODUCTION (Odoo.sh / funedistri.odoo.com)
# =====================================================================
# This is a SEPARATE, throwaway module whose only job is to seed a local dev
# database with test B2B accounts (fake companies + users) so we can click
# through the store in both roles without hand-creating them every time.
#
# WHY A SEPARATE MODULE (and not demo data in the main module)?
#   Odoo's demo system is a GLOBAL on/off switch (`--with-demo`). Turning it on
#   to load OUR seed would ALSO load every other module's demo data — Odoo's
#   sample furniture products, sample customers, etc. The owner wants a CLEAN
#   local DB with ONLY our seed. Odoo has no "load demo for just one module"
#   flag (`--without-demo` is a plain boolean in this build).
#   So instead we keep global demo OFF and put the seed in this module's regular
#   `data` (which always loads when the module is INSTALLED). We then install
#   this module ONLY locally, from the Makefile. Prod never installs it, so the
#   fake accounts can never leak into production.
#
# HOW IT STAYS OUT OF PROD
#   On Odoo.sh you choose which modules a database installs; a module merely
#   sitting in the repo is NOT installed unless selected or marked auto_install.
#   This one is auto_install=False and is never added to the prod DB. The
#   Makefile installs it explicitly for local dev only.
{
    "name": "Funedistri DEV SEED (local only — do not install on prod)",
    "version": "1.0.0",
    "summary": "Local-only test B2B companies + users. Never install on production.",
    "category": "Hidden",
    "author": "Funedistri",
    "license": "LGPL-3",
    # Depends on the main module: the seed sets `b2b_role`, a field that module
    # adds to res.partner/res.users, and relies on its create() sync to drop
    # each user into the right hidden security group.
    "depends": [
        "funedistri_customizations",
    ],
    # Regular data (NOT demo): loads whenever this module is installed. Because
    # we only ever install this module locally, the seed only exists locally.
    "data": [
        # Coffin Options (native attributes + values + extra prices), captured
        # from the Owner's hand-built config so the configurator rebuilds itself.
        "data/seed_coffin_attributes.xml",
        # A published, configurable Coffin model wired to those Options, so the
        # shop has a real coffin to build + submit. Loads AFTER the attributes it
        # references.
        "data/seed_coffin_product.xml",
        # NOTE: test B2B companies + users (seed_b2b_users.xml) were removed at the
        # 2026-06-15 reset — they set b2b_role, a field the main module no longer
        # defines. Restore this seed when step 2 (Roles foundation) re-adds b2b_role.
    ],
    "installable": True,
    # auto_install=False → never installs itself; must be asked for explicitly
    # (our Makefile does, prod never does).
    "auto_install": False,
    "application": False,
}
