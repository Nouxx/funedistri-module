# -*- coding: utf-8 -*-
"""Step 1 tracer-spine tests: submitting a cart makes a Pending Order + notifies.

Unit level (TransactionCase) — exercises the model behaviour without the website,
so it's fast and doesn't need a browser. The controller just calls the model
method tested here.
"""

from odoo.tests import TransactionCase, tagged


# post_install: run against the fully-installed registry (all deps loaded).
# -at_install: don't run mid-install (the website/sale machinery must be ready).
@tagged('post_install', '-at_install')
class TestSubmitOrder(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # A customer (stands in for a B2B user's company) and a sellable product.
        cls.partner = cls.env['res.partner'].create({'name': 'Test Company'})
        cls.product = cls.env['product.product'].create({
            'name': 'Cercueil Test',
            'list_price': 500.0,
            'sale_ok': True,
        })

    def _make_draft_order(self):
        """A plain draft sale.order with one line — i.e. a 'cart'."""
        return self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 1,
            })],
        })

    def test_submit_flags_pending(self):
        """A fresh cart is not submitted; after submit it is (and stays draft)."""
        order = self._make_draft_order()
        self.assertFalse(order.coffin_is_submitted,
                         "a fresh cart must not be marked submitted")

        order._coffin_submit_as_pending()

        self.assertTrue(order.coffin_is_submitted,
                        "submit must flag the Order as Pending")
        self.assertEqual(order.state, 'draft',
                         "Pending Order must stay draft until the Owner Validates")

    def test_submit_schedules_owner_activity(self):
        """Submit schedules a 'To Do' activity on the Order for the Owner."""
        order = self._make_draft_order()
        order._coffin_submit_as_pending()

        activities = self.env['mail.activity'].search([
            ('res_model', '=', 'sale.order'),
            ('res_id', '=', order.id),
        ])
        self.assertTrue(
            activities,
            "submit must schedule an activity so no Order sits unseen",
        )
