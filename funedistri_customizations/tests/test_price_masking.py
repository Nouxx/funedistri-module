# -*- coding: utf-8 -*-
"""Step 4 audit — "no price anywhere" for a Salesman (ADR 0001).

Proves the guardrail across the surfaces the server controls:
  1. JSON cart/delivery routes never emit the real number for a Salesman;
  2. rendered HTML (product page, cart) shows "Prix masqué", never a price;
  3. the portal order DETAIL page is blocked for a Salesman (→ order list);
and that none of it fires for a Store owner (masking is role-targeted).

HttpCase (url_open / jsonrpc — no browser) so routes, sessions and QWeb `groups=`
run as for a real browser.
"""

import re

from odoo.tests import HttpCase, tagged

from .common import CoffinFixtureMixin, SALESMAN_LOGIN, STORE_OWNER_LOGIN

_MASK_TEXT = 'Prix masqué'
_MASK_MARK = 'coffin-price-masked'   # CSS class on the masked-amount placeholder
_CURRENCY_RE = re.compile(r'oe_currency_value">\s*([\d.,]+)\s*<')


def _rendered_a_real_price(html):
    """True if the HTML renders at least one non-zero monetary amount."""
    for raw in _CURRENCY_RE.findall(html):
        if float(raw.replace(',', '')) > 0.0:
            return True
    return False


@tagged('post_install', '-at_install')
class TestPriceMasking(CoffinFixtureMixin, HttpCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        assert cls.salesman.has_group(
            'funedistri_customizations.coffin_salesman_group')
        assert cls.store_owner.has_group(
            'funedistri_customizations.coffin_store_owner_group')

    def _add_one_coffin(self):
        return self.make_jsonrpc_request('/shop/cart/add', {
            'product_template_id': self.coffin.id,
            'product_id': self.coffin_variant.id,
            'quantity': 1,
        })

    def _delivery_method_id(self, partner):
        order = self.env['sale.order'].search(
            [('partner_id', '=', partner.id)], order='id desc', limit=1)
        dm_ids = order._get_delivery_methods().ids
        if not dm_ids:
            self.skipTest("no delivery method available for the test cart")
        return dm_ids[0]

    # ---------------- Salesman: every server surface is money-free ----------- #
    def test_salesman_json_routes_emit_no_price(self):
        self.authenticate(SALESMAN_LOGIN, SALESMAN_LOGIN)
        add = self._add_one_coffin()
        for line in add.get('notification_info', {}).get('lines', []):
            self.assertEqual(line.get('price_total'), 0.0)
        for item in add.get('tracking_info', []):
            self.assertEqual(item.get('price'), 0.0)
            self.assertEqual(item.get('discount'), 0.0)

        order = self.env['sale.order'].search(
            [('partner_id', '=', self.salesman.partner_id.id)], limit=1)
        upd = self.make_jsonrpc_request('/shop/cart/update', {
            'line_id': order.order_line[0].id, 'quantity': 2})
        self.assertEqual(upd.get('amount'), 0.0)
        self.assertEqual(upd.get('minor_amount'), 0)

    def test_salesman_html_shows_placeholder_not_price(self):
        self.authenticate(SALESMAN_LOGIN, SALESMAN_LOGIN)
        self._add_one_coffin()
        for url in (self.coffin.website_url, '/shop/cart'):
            html = self.url_open(url).text
            self.assertIn(_MASK_TEXT, html,
                          f"Salesman must see the masked placeholder on {url}")
        cart_html = self.url_open('/shop/cart').text
        self.assertFalse(_rendered_a_real_price(cart_html),
                         "Salesman must never see a rendered price on /shop/cart")

    def test_salesman_delivery_routes_emit_no_price(self):
        self.authenticate(SALESMAN_LOGIN, SALESMAN_LOGIN)
        self._add_one_coffin()
        dm_id = self._delivery_method_id(self.salesman.partner_id)
        summary = self.make_jsonrpc_request('/shop/set_delivery_method', {'dm_id': dm_id})
        for key in ('amount_delivery', 'amount_untaxed', 'amount_tax', 'amount_total'):
            self.assertIn(_MASK_MARK, str(summary.get(key, '')),
                          f"Salesman set_delivery_method must mask {key}")
            self.assertNotIn('oe_currency_value', str(summary.get(key, '')))
        rate = self.make_jsonrpc_request('/shop/get_delivery_rate', {'dm_id': dm_id})
        self.assertEqual(rate.get('price'), 0.0)
        self.assertIn(_MASK_MARK, str(rate.get('amount_delivery', '')))

    def test_salesman_portal_order_detail_blocked(self):
        # A submitted Pending Order for the salesman.
        order = self.env['sale.order'].create({
            'partner_id': self.salesman.partner_id.id,
            'order_line': [(0, 0, {'product_id': self.coffin_variant.id,
                                   'product_uom_qty': 1})],
        })
        order._coffin_submit_as_pending()
        self.authenticate(SALESMAN_LOGIN, SALESMAN_LOGIN)
        # Detail page → redirected to the order list (no priced document).
        resp = self.url_open(f'/my/orders/{order.id}', allow_redirects=True)
        self.assertTrue(resp.url.endswith('/my/orders'),
                        "Salesman order detail must redirect to the order list")
        # PDF report → also blocked.
        pdf = self.url_open(f'/my/orders/{order.id}?report_type=pdf',
                            allow_redirects=True)
        self.assertTrue(pdf.url.endswith('/my/orders'),
                        "Salesman must not download the order PDF")

    # ---------------- Store owner: masking must NOT fire --------------------- #
    def test_store_owner_sees_real_price(self):
        self.authenticate(STORE_OWNER_LOGIN, STORE_OWNER_LOGIN)
        self._add_one_coffin()
        order = self.env['sale.order'].search(
            [('partner_id', '=', self.store_owner.partner_id.id)], limit=1)
        upd = self.make_jsonrpc_request('/shop/cart/update', {
            'line_id': order.order_line[0].id, 'quantity': 1})
        self.assertGreater(upd.get('amount'), 0.0)
        html = self.url_open('/shop/cart').text
        self.assertNotIn(_MASK_TEXT, html)
        self.assertTrue(_rendered_a_real_price(html))

    def test_store_owner_portal_detail_accessible(self):
        order = self.env['sale.order'].create({
            'partner_id': self.store_owner.partner_id.id,
            'order_line': [(0, 0, {'product_id': self.coffin_variant.id,
                                   'product_uom_qty': 1})],
        })
        order._coffin_submit_as_pending()
        self.authenticate(STORE_OWNER_LOGIN, STORE_OWNER_LOGIN)
        resp = self.url_open(f'/my/orders/{order.id}', allow_redirects=True)
        self.assertIn(f'/my/orders/{order.id}', resp.url,
                      "Store owner must reach the order detail page")
