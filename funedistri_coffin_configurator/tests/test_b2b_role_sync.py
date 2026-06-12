# -*- coding: utf-8 -*-
"""Step 2.5 — server-truth test for the b2b_role -> security-group sync.

Invariant: editing the ONE ``b2b_role`` dropdown on a contact keeps the hidden
security groups on its linked user(s) correct — on set, on change, and on clear.
This is the hook every later price-hiding branch relies on, so it must be exact.
"""

from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestB2bRoleSync(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.salesman_group = cls.env.ref(
            'funedistri_coffin_configurator.coffin_salesman_group'
        )
        cls.store_owner_group = cls.env.ref(
            'funedistri_coffin_configurator.coffin_store_owner_group'
        )
        # A portal user whose contact (partner) will carry the role.
        cls.user = cls.env['res.users'].create({
            'name': 'Role Sync User',
            'login': 'role_sync_user',
            'group_ids': [(6, 0, [cls.env.ref('base.group_portal').id])],
        })
        cls.partner = cls.user.partner_id

    def test_set_change_clear_resyncs_group(self):
        # --- set: salesman ---
        self.partner.b2b_role = 'salesman'
        self.assertTrue(self.user.has_group(
            'funedistri_coffin_configurator.coffin_salesman_group'))
        self.assertFalse(self.user.has_group(
            'funedistri_coffin_configurator.coffin_store_owner_group'))

        # --- change: store_owner (the other group, and salesman dropped) ---
        self.partner.b2b_role = 'store_owner'
        self.assertTrue(self.user.has_group(
            'funedistri_coffin_configurator.coffin_store_owner_group'))
        self.assertFalse(self.user.has_group(
            'funedistri_coffin_configurator.coffin_salesman_group'))

        # --- clear: neither group remains ---
        self.partner.b2b_role = False
        self.assertFalse(self.user.has_group(
            'funedistri_coffin_configurator.coffin_salesman_group'))
        self.assertFalse(self.user.has_group(
            'funedistri_coffin_configurator.coffin_store_owner_group'))

    def test_user_created_after_role_inherits_group(self):
        # Role set on a contact that has NO user yet...
        contact = self.env['res.partner'].create({
            'name': 'Pre-roled Contact',
            'b2b_role': 'salesman',
        })
        # ...then a login user is created for that contact.
        new_user = self.env['res.users'].create({
            'name': 'Late User',
            'login': 'late_user',
            'partner_id': contact.id,
            'group_ids': [(6, 0, [self.env.ref('base.group_portal').id])],
        })
        # res.users.create sync must have granted the matching group.
        self.assertTrue(new_user.has_group(
            'funedistri_coffin_configurator.coffin_salesman_group'))
