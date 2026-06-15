# -*- coding: utf-8 -*-
"""Server-truth checks on the configurable coffin + company shape.

Two invariants worth locking (built from CoffinFixtureMixin, no demo seed):
  1. The Store owner and Salesman share ONE commercial_partner_id (the company)
     — this is what makes native company-scoped order visibility work.
  2. The configurable coffin's priced options carry the expected price_extra,
     and its attributes are 'no_variant' (no SKU explosion).
"""

from odoo.tests import TransactionCase, tagged

from .common import CoffinFixtureMixin


@tagged('post_install', '-at_install')
class TestCatalog(CoffinFixtureMixin, TransactionCase):

    def test_b2b_users_share_company(self):
        # Both users' contacts roll up to the same commercial partner = company.
        self.assertEqual(self.store_owner.partner_id.commercial_partner_id, self.company)
        self.assertEqual(self.salesman.partner_id.commercial_partner_id, self.company)
        self.assertEqual(
            self.store_owner.partner_id.commercial_partner_id,
            self.salesman.partner_id.commercial_partner_id,
            "B2B users must share one commercial_partner_id (the company)",
        )

    def test_coffin_option_prices(self):
        # price_extra lives on the auto-created PTAVs.
        self.assertEqual(self.ptav_plywood.price_extra, 120.0)
        self.assertEqual(self.ptav_gold.price_extra, 80.0)
        self.assertEqual(self.ptav_oak.price_extra, 0.0, "Base option stays +0")

    def test_coffin_uses_no_variant_attributes(self):
        # The whole point: no SKU explosion — attributes are 'no_variant'.
        for line in self.coffin.attribute_line_ids:
            self.assertEqual(line.attribute_id.create_variant, 'no_variant')
