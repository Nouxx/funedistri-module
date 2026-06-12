# -*- coding: utf-8 -*-
"""Step 1.6 — server-truth test for the tracer submit pipe.

The invariant we protect (per the implementation plan's "test the truth"):
submitting the cart leaves a ``sale.order`` in the ``draft`` state (= our
*Pending*), and detaches it from the live cart session — WITHOUT confirming it
(no jump to ``state='sale'``; that is the Owner's job later).

We use ``HttpCase`` because the behaviour lives in an HTTP controller that
depends on ``request`` (the session cart). HttpCase spins up a real server we
can drive over HTTP, exactly as a browser would: log in, add to cart, submit.
"""

import re

from odoo.tests import HttpCase, tagged


# post_install: run after all modules are installed (the website + routes exist).
# -at_install: do NOT run during installation (the server isn't fully up then).
@tagged('post_install', '-at_install')
class TestSubmitOrder(HttpCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # The tracer coffin loaded from data/tracer_coffin.xml. Its auto-created
        # variant (product.product) is what actually goes on an order line.
        cls.coffin = cls.env.ref(
            'funedistri_coffin_configurator.product_tracer_coffin'
        )
        cls.coffin_variant = cls.coffin.product_variant_id

        # A B2B-like portal user with a COMPLETE address — the checkout guard
        # (_check_addresses) redirects away if billing/delivery is incomplete,
        # so the submit would never run. France/euros matches our locale.
        cls.portal_user = cls.env['res.users'].create({
            'name': 'Test Salesman',
            'login': 'test_b2b',
            'password': 'test_b2b',
            # v19 renamed res.users.groups_id -> group_ids.
            'group_ids': [(6, 0, [cls.env.ref('base.group_portal').id])],
            # Mandatory checkout address fields (portal._get_mandatory_delivery_
            # address_fields): name, email, phone, street, city, country, zip.
            'email': 'test_b2b@example.com',
            'phone': '+33100000000',
            'street': '1 rue du Test',
            'city': 'Paris',
            'zip': '75001',
            'country_id': cls.env.ref('base.fr').id,
        })

    def _csrf_token(self):
        """Pull a valid CSRF token for the current session.

        Our /shop/submit_order is a POST, so Odoo requires the session's CSRF
        token. Any rendered website page embeds one in its forms; we scrape it
        from the cart page (already authenticated at this point).
        """
        html = self.url_open('/shop/cart').text
        # The token is embedded as JS: `csrf_token: "<hex>o<timestamp>"` — note
        # it is NOT pure hex (an 'o' separates the body from a timestamp).
        match = re.search(r'csrf_token["\s:]+["\']([^"\']+)["\']', html)
        self.assertTrue(match, "Could not find a CSRF token on /shop/cart")
        return match.group(1)

    def test_submit_leaves_order_in_draft(self):
        # Log in as the portal user; subsequent requests reuse this session.
        self.authenticate('test_b2b', 'test_b2b')

        # Build the cart: add one tracer coffin. This creates the draft
        # sale.order behind the session (the cart IS the order).
        self.make_jsonrpc_request('/shop/cart/add', {
            'product_template_id': self.coffin.id,
            'product_id': self.coffin_variant.id,
            'quantity': 1,
        })

        # The cart order now exists for this partner, in draft.
        order = self.env['sale.order'].search([
            ('partner_id', '=', self.portal_user.partner_id.id),
        ])
        self.assertEqual(len(order), 1, "Exactly one cart order should exist")
        self.assertEqual(order.state, 'draft')
        self.assertEqual(order.order_line.product_id, self.coffin_variant)

        # Submit the order (flow A — no payment).
        response = self.url_open(
            '/shop/submit_order',
            data={'csrf_token': self._csrf_token()},
            allow_redirects=False,
        )

        # Submit redirects to the confirmation page...
        self.assertIn(response.status_code, (302, 303))
        self.assertIn('/shop/confirmation', response.headers.get('Location', ''))

        # ...and the KEY invariant: the order is STILL draft (Pending), not
        # confirmed. The Owner validates it later.
        order.invalidate_recordset()
        self.assertEqual(
            order.state, 'draft',
            "Submit must leave the order Pending (draft), never confirm it",
        )

        # The submit marker is set: this draft is a Pending Order, not a cart.
        self.assertTrue(
            order.coffin_is_submitted,
            "Submit must flag the order as submitted (Pending)",
        )

        # And it now surfaces in the B2B user's portal Orders list (the domain
        # override includes submitted drafts). The native list would hide it.
        my_orders = self.url_open('/my/orders').text
        self.assertIn(
            order.name, my_orders,
            "Submitted Pending Order must appear in /my/orders",
        )
