# -*- coding: utf-8 -*-
"""Step 5 — locked company address book (ADR 0005).

A B2B user may only SELECT among their company's Owner-defined DELIVERY addresses:
no create/edit form, and the selected delivery address must be one of the allowed
set. Billing is untouched. Server-enforced.
"""

from odoo.tests import HttpCase, TransactionCase, tagged

from .common import CoffinFixtureMixin, SALESMAN_LOGIN


@tagged('post_install', '-at_install')
class TestB2bUserHelper(CoffinFixtureMixin, TransactionCase):

    def test_b2b_user_flag(self):
        self.assertTrue(self.salesman._coffin_is_b2b_user())
        self.assertTrue(self.store_owner._coffin_is_b2b_user())
        orphan = self.env['res.users'].create({
            'name': 'No Role', 'login': 'al_orphan',
            'group_ids': [(6, 0, [self.env.ref('base.group_portal').id])]})
        self.assertFalse(orphan._coffin_is_b2b_user())
        self.assertFalse(self.env.ref('base.user_admin')._coffin_is_b2b_user())


@tagged('post_install', '-at_install')
class TestAddressLock(CoffinFixtureMixin, HttpCase):

    def _login_with_cart(self):
        self.authenticate(SALESMAN_LOGIN, SALESMAN_LOGIN)
        self.make_jsonrpc_request('/shop/cart/add', {
            'product_template_id': self.coffin.id,
            'product_id': self.coffin_variant.id, 'quantity': 1})

    def test_delivery_address_form_blocked(self):
        self._login_with_cart()
        resp = self.url_open('/shop/address?address_type=delivery',
                             allow_redirects=True)
        self.assertTrue(resp.url.endswith('/shop/checkout'),
                        "B2B user must not reach the delivery address form")

    def test_billing_address_form_allowed(self):
        self._login_with_cart()
        resp = self.url_open('/shop/address?address_type=billing',
                             allow_redirects=True)
        self.assertNotIn('/shop/checkout', resp.url,
                         "billing address form stays available (delivery-only lock)")

    def test_select_allowed_delivery_address(self):
        self._login_with_cart()
        # Selecting a company delivery address succeeds and sets it on the order.
        self.make_jsonrpc_request('/shop/update_address', {
            'partner_id': self.delivery_addr.id, 'address_type': 'delivery'})
        order = self.env['sale.order'].search(
            [('partner_id', '=', self.salesman.partner_id.id)], order='id desc', limit=1)
        self.assertEqual(order.partner_shipping_id, self.delivery_addr)

    def test_select_rogue_delivery_address_refused(self):
        self._login_with_cart()
        # A delivery address that is NOT one of the company's is refused (403).
        with self.assertRaises(Exception):
            self.make_jsonrpc_request('/shop/update_address', {
                'partner_id': self.rogue_addr.id, 'address_type': 'delivery'})
