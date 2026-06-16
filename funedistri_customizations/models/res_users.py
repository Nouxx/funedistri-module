# -*- coding: utf-8 -*-
"""Keep a newly-created user's groups in sync with its contact's b2b_role (Step 2).

The role is set on the contact (res.partner). The Owner often sets it BEFORE the
login user exists (e.g. configures the company's contacts, then those people get
portal accounts). So when a user is created, we re-run the partner sync so the new
user immediately lands in the right hidden group.
"""

from odoo import api, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.model_create_multi
    def create(self, vals_list):
        users = super().create(vals_list)
        # The new users' contacts may already carry a b2b_role; reconcile groups.
        # mapped/recordset partner_id dedupes, then the partner method syncs all
        # its linked users (including these fresh ones).
        users.partner_id._sync_b2b_role_to_users()
        return users
