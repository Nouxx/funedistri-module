# -*- coding: utf-8 -*-
"""Step 3 — login gate (ADR 0003).

Locks the two invariants: the shop is gated to logged-in users (public has no
eCommerce access), and public self-signup is off.
"""

from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestLoginGate(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.website = cls.env['website'].search([], limit=1)
        cls.public_user = cls.env.ref('base.public_user')
        cls.portal_user = cls.env['res.users'].create({
            'name': 'Gate Portal User', 'login': 'gate_portal',
            'group_ids': [(6, 0, [cls.env.ref('base.group_portal').id])],
        })

    def test_shop_gated_to_logged_in(self):
        self.assertEqual(self.website.ecommerce_access, 'logged_in',
                         "shop must be restricted to logged-in users")

    def test_public_has_no_ecommerce_access(self):
        # has_ecommerce_access() is what the shop/cart/product controllers check
        # before serving (they redirect the public to /web/login otherwise).
        website_public = self.website.with_user(self.public_user)
        self.assertFalse(website_public.has_ecommerce_access(),
                         "the public user must NOT reach the shop")

    def test_logged_in_user_has_ecommerce_access(self):
        website_portal = self.website.with_user(self.portal_user)
        self.assertTrue(website_portal.has_ecommerce_access(),
                        "a logged-in portal user must reach the shop")

    def test_no_public_self_signup(self):
        scope = self.env['ir.config_parameter'].sudo().get_param(
            'auth_signup.invitation_scope')
        self.assertEqual(scope, 'b2b',
                         "public self-registration must be off (invitation only)")
