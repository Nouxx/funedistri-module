# -*- coding: utf-8 -*-
"""Step 5 + 5b — locked company address book (ADR 0005).

A B2B user creates/edits NO address (checkout or portal). They select only among
the company's addresses, with strict type separation: shipping ← Delivery contacts,
billing ← Invoice contacts; neither crosses; their own contact is never selectable.
Server-enforced.
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

    def _update_address(self, partner, address_type):
        return self.make_jsonrpc_request('/shop/update_address', {
            'partner_id': partner.id, 'address_type': address_type})

    # --- no create/edit form, at checkout or portal --- #
    def test_checkout_delivery_form_blocked(self):
        self._login_with_cart()
        resp = self.url_open('/shop/address?address_type=delivery', allow_redirects=True)
        self.assertTrue(resp.url.endswith('/shop/checkout'))

    def test_checkout_billing_form_blocked(self):
        self._login_with_cart()
        resp = self.url_open('/shop/address?address_type=billing', allow_redirects=True)
        self.assertTrue(resp.url.endswith('/shop/checkout'),
                        "billing address form is also blocked (Step 5b)")

    def test_portal_address_form_blocked(self):
        self.authenticate(SALESMAN_LOGIN, SALESMAN_LOGIN)
        resp = self.url_open('/my/address?address_type=billing', allow_redirects=True)
        self.assertTrue(resp.url.endswith('/my/addresses'),
                        "portal address form is blocked too")

    def test_portal_address_archive_blocked(self):
        self.authenticate(SALESMAN_LOGIN, SALESMAN_LOGIN)
        with self.assertRaises(Exception):
            self.make_jsonrpc_request('/my/address/archive',
                                      {'partner_id': self.invoice_addr.id})

    def test_checkout_billing_block_marked_disabled(self):
        # The checkout billing block is marked so CSS disables the "Same as
        # delivery address" toggle for a B2B user.
        self._login_with_cart()
        html = self.url_open('/shop/checkout', allow_redirects=True).text
        self.assertIn('coffin-addr-locked', html,
                      "checkout billing block must be marked disabled for B2B")

    def test_portal_address_controls_visually_disabled(self):
        # The /my/addresses action controls are marked disabled for a B2B user
        # (the CSS class on the section drives the visual disable).
        self.authenticate(SALESMAN_LOGIN, SALESMAN_LOGIN)
        html = self.url_open('/my/addresses').text
        self.assertIn('coffin-addr-locked', html,
                      "B2B user's address controls must be marked disabled")

    # --- selection: right type only, strictly separated --- #
    def test_select_allowed_delivery_and_billing(self):
        self._login_with_cart()
        self._update_address(self.delivery_addr, 'delivery')
        self._update_address(self.invoice_addr, 'billing')
        order = self.env['sale.order'].search(
            [('partner_id', '=', self.salesman.partner_id.id)], order='id desc', limit=1)
        self.assertEqual(order.partner_shipping_id, self.delivery_addr)
        self.assertEqual(order.partner_invoice_id, self.invoice_addr)

    def test_invoice_address_not_shippable(self):
        self._login_with_cart()
        with self.assertRaises(Exception):
            self._update_address(self.invoice_addr, 'delivery')

    def test_delivery_address_not_billable(self):
        self._login_with_cart()
        with self.assertRaises(Exception):
            self._update_address(self.delivery_addr, 'billing')

    def test_rogue_address_refused(self):
        self._login_with_cart()
        with self.assertRaises(Exception):
            self._update_address(self.rogue_addr, 'delivery')
