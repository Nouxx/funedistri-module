# -*- coding: utf-8 -*-
"""B2B role on the contact, and the field -> security-group sync (Step 2, ADR 0003).

Design ("field-drives-group"): the Owner edits ONE dropdown, ``b2b_role``, on a
contact. Behind the scenes we keep the matching hidden security group in sync on
every user linked to that contact, so price-hiding code (Step 4) can branch on the
conventional, cache-friendly ``has_group(...)`` check.

The role lives on ``res.partner`` (the contact) but Odoo security groups live on
``res.users``. A B2B user is a ``res.users`` whose ``partner_id`` points at the
contact, so the sync target is ``partner.user_ids``.

GUARDRAIL (ADR 0003): the sync only ever toggles the two coffin groups — never an
internal group — so a B2B user always stays a portal user (backend stays locked).
"""

from odoo import fields, models
from odoo.fields import Command


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # The single field the Owner edits. Optional: a plain contact / a customer
    # company itself has no role (only the people who log in to shop do).
    b2b_role = fields.Selection(
        selection=[
            ('salesman', "Salesman"),
            ('store_owner', "Store owner"),
        ],
        string="B2B role",
        help="Role of this B2B user in the coffin shop. "
             "Salesman: places orders, sees NO prices. "
             "Store owner: places orders and sees prices. "
             "Leave empty for a company or a non-shopping contact.",
    )

    def write(self, vals):
        # Let the normal write happen first, THEN reconcile groups — so we sync
        # against the value actually stored. Only bother when b2b_role changed.
        res = super().write(vals)
        if 'b2b_role' in vals:
            self._sync_b2b_role_to_users()
        return res

    def _sync_b2b_role_to_users(self):
        """Make each linked user's group membership match its contact's role.

        Idempotent: adds the group that matches ``b2b_role`` and removes the
        other, so setting / changing / clearing the field all converge to the
        right state. A contact with no linked user is a no-op (a user created
        later picks it up via res.users.create).
        """
        salesman_group = self.env.ref(
            'funedistri_customizations.coffin_salesman_group'
        )
        store_owner_group = self.env.ref(
            'funedistri_customizations.coffin_store_owner_group'
        )

        for partner in self:
            users = partner.user_ids
            if not users:
                continue

            if partner.b2b_role == 'salesman':
                add, remove = salesman_group, store_owner_group
            elif partner.b2b_role == 'store_owner':
                add, remove = store_owner_group, salesman_group
            else:
                # Cleared: strip both roles.
                add, remove = self.env['res.groups'], salesman_group | store_owner_group

            # Command.link adds, Command.unlink removes — applied to the users'
            # group_ids (v19 field name; was groups_id pre-19). We touch ONLY the
            # two coffin groups, never base.group_user — the portal lockout holds.
            commands = [Command.link(g.id) for g in add]
            commands += [Command.unlink(g.id) for g in remove]
            if commands:
                users.write({'group_ids': commands})
