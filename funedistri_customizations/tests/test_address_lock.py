# -*- coding: utf-8 -*-
"""Step 5 + 5b — locked company address book (ADR 0005).

A B2B user creates/edits NO address (checkout or portal). They select only among
the company's addresses, with strict type separation: shipping ← Delivery contacts,
billing ← Invoice contacts; neither crosses; their own contact is never selectable.
Server-enforced.
"""

import re

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

    def test_own_address_hidden_at_checkout(self):
        # The checkout address lists show only the company's Invoice/Delivery
        # contacts — never the logged-in user's own contact (redundant).
        self._login_with_cart()
        html = self.url_open('/shop/checkout', allow_redirects=True).text
        card_ids = set(re.findall(r'data-partner-id="(\d+)"', html))
        self.assertIn(str(self.delivery_addr.id), card_ids,
                      "company delivery address must be selectable")
        self.assertIn(str(self.invoice_addr.id), card_ids,
                      "company invoice address must be selectable")
        self.assertNotIn(str(self.salesman.partner_id.id), card_ids,
                         "the user's own contact must NOT be a selectable address")


@tagged('post_install', '-at_install')
class TestAddressBlockOnMissing(CoffinFixtureMixin, HttpCase):
    """A B2B user whose company lacks a required address type reaches checkout
    with the continue button DISABLED + a notice — not a bounce to the cart."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        env = cls.env
        addr = {'street': '1 rue X', 'city': 'Lyon', 'zip': '69000',
                'country_id': env.ref('base.fr').id}
        # Company with a Delivery address but NO Invoice address.
        co = env['res.partner'].create({
            'name': 'NoInvoice Co', 'is_company': True,
            'email': 'c@noinv.test', **addr})
        env['res.partner'].create({
            'name': 'Livraison', 'parent_id': co.id, 'type': 'delivery',
            'email': 'd@noinv.test', 'phone': '+33100000001', **addr})
        cls.ni_user = env['res.users'].create({
            'name': 'NI Salesman', 'login': 'ni_salesman', 'password': 'ni_salesman',
            'group_ids': [(6, 0, [env.ref('base.group_portal').id])],
            'parent_id': co.id, 'b2b_role': 'salesman',
            'email': 'ni@noinv.test', 'phone': '+33100000002', **addr})

    def test_blocked_company_reaches_checkout_button_disabled(self):
        self.authenticate('ni_salesman', 'ni_salesman')
        self.make_jsonrpc_request('/shop/cart/add', {
            'product_template_id': self.coffin.id,
            'product_id': self.coffin_variant.id, 'quantity': 1})
        resp = self.url_open('/shop/checkout', allow_redirects=True)
        # Renders checkout (not bounced to /shop/cart).
        self.assertTrue(resp.url.endswith('/shop/checkout'))
        # Explanatory notice shown.
        self.assertIn('Aucune adresse de facturation', resp.text)
        # The continue button is rendered disabled AND genuinely unclickable
        # (aria-disabled + href neutralised), not just greyed.
        self.assertTrue(
            re.search(r'website_sale_main_button[^>]*\bdisabled\b', resp.text),
            "the checkout continue button must be disabled")
        self.assertTrue(
            re.search(r'website_sale_main_button[^>]*aria-disabled="true"', resp.text),
            "the disabled button must be truly unclickable (aria-disabled)")

    def test_blocked_flag_on_order(self):
        order = self.env['sale.order'].create({
            'partner_id': self.ni_user.partner_id.id,
            'order_line': [(0, 0, {'product_id': self.coffin_variant.id,
                                   'product_uom_qty': 1})]})
        self.assertTrue(order._coffin_addresses_blocked(),
                        "company without an invoice address is blocked")
