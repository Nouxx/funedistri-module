# -*- coding: utf-8 -*-
"""Company-scoped order visibility, incl. the orphan-user guarantee (plan Step 6).

Native Odoo scopes portal orders by ``commercial_partner_id``. We rely on that
(no custom rule). These tests lock the two guarantees we care about:
  - a B2B user sees their OWN company's orders, never another company's;
  - an ORPHAN user (in no company) sees NO orders — its commercial_partner is
    itself, so it can never see anyone else's. (It must NOT see everything.)

Fixtures are built here (not from the dev seed) so the test stands alone.
"""

from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestOrderVisibility(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        portal = cls.env.ref('base.group_portal')
        cls.product = cls.env['product.product'].create({
            'name': 'Cercueil Test', 'list_price': 500.0, 'sale_ok': True,
        })

        # Company A + a salesman under it (parent_id = the company).
        cls.company_a = cls.env['res.partner'].create({
            'name': 'Company A', 'is_company': True,
        })
        cls.user_a = cls.env['res.users'].create({
            'name': 'A Salesman', 'login': 'vis_a_salesman',
            'group_ids': [(6, 0, [portal.id])],
            'parent_id': cls.company_a.id,
        })
        # Company B + a salesman (different company).
        cls.company_b = cls.env['res.partner'].create({
            'name': 'Company B', 'is_company': True,
        })
        cls.user_b = cls.env['res.users'].create({
            'name': 'B Salesman', 'login': 'vis_b_salesman',
            'group_ids': [(6, 0, [portal.id])],
            'parent_id': cls.company_b.id,
        })
        # Orphan: portal user with NO parent → commercial_partner is itself.
        cls.user_orphan = cls.env['res.users'].create({
            'name': 'Orphan', 'login': 'vis_orphan',
            'group_ids': [(6, 0, [portal.id])],
        })

        # A Pending Order placed by Company A's salesman.
        cls.order_a = cls.env['sale.order'].create({
            'partner_id': cls.user_a.partner_id.id,
            'order_line': [(0, 0, {'product_id': cls.product.id,
                                   'product_uom_qty': 1})],
        })
        cls.order_a._coffin_submit_as_pending()

    def _visible_to(self, user):
        # search() applies the user's record rules → only what they may read.
        return self.env['sale.order'].with_user(user).search([])

    def test_same_company_sees_its_order(self):
        self.assertIn(self.order_a, self._visible_to(self.user_a),
                      "a B2B user must see their own company's Order")

    def test_other_company_cannot_see_it(self):
        self.assertNotIn(self.order_a, self._visible_to(self.user_b),
                         "a user must NEVER see another company's Order")

    def test_orphan_sees_nothing(self):
        visible = self._visible_to(self.user_orphan)
        self.assertNotIn(self.order_a, visible,
                         "orphan must not see another company's Order")
        self.assertFalse(visible,
                         "orphan (no company) must see NO orders at all")
