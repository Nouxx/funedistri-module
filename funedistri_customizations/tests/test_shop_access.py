# -*- coding: utf-8 -*-
"""Step 3+ — only configured B2B users (or staff) may shop.

An orphan portal user (no company/role) must NOT reach the shop. We test the
decision method res.users._coffin_can_shop() directly (the shop-entry controllers
redirect denied users to /my); this keeps the test fast and web-free.
"""

from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestShopAccess(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        portal = cls.env.ref('base.group_portal')

        # Orphan: portal, no company, no role.
        cls.orphan = cls.env['res.users'].create({
            'name': 'Shop Orphan', 'login': 'shop_orphan',
            'group_ids': [(6, 0, [portal.id])],
        })
        # Salesman: portal under a company, b2b_role drives the group.
        company = cls.env['res.partner'].create({'name': 'Shop Co', 'is_company': True})
        cls.salesman = cls.env['res.users'].create({
            'name': 'Shop Salesman', 'login': 'shop_salesman',
            'group_ids': [(6, 0, [portal.id])], 'parent_id': company.id,
        })
        cls.salesman.partner_id.b2b_role = 'salesman'

    def test_orphan_cannot_shop(self):
        self.assertFalse(self.orphan._coffin_can_shop(),
                         "orphan (no company/role) must not reach the shop")

    def test_b2b_user_can_shop(self):
        self.assertTrue(self.salesman._coffin_can_shop(),
                        "a configured B2B user must reach the shop")

    def test_internal_staff_can_shop(self):
        self.assertTrue(self.env.ref('base.user_admin')._coffin_can_shop(),
                        "internal staff (the Owner) may preview the shop")

    def test_public_not_denied_here(self):
        # Public returns True here so they fall through to the native login gate
        # (Step 3) rather than being redirected to /my.
        self.assertTrue(self.env.ref('base.public_user')._coffin_can_shop())
