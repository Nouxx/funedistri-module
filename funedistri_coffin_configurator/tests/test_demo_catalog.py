# -*- coding: utf-8 -*-
"""Step 3.4 — server-truth checks on the demo catalog + company shape.

Two invariants worth locking:
  1. The demo Store owner and Salesman share ONE commercial_partner_id (the
     company) — this is what makes native company-scoped order visibility work.
  2. The configurable coffin's priced options carry the expected price_extra
     (the _update_xmlids trick actually wired the prices onto the right PTAVs).
"""

from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestDemoCatalog(TransactionCase):

    def test_demo_b2b_users_share_company(self):
        company = self.env.ref('funedistri_coffin_configurator.demo_company')
        store_owner = self.env.ref(
            'funedistri_coffin_configurator.demo_user_store_owner')
        salesman = self.env.ref(
            'funedistri_coffin_configurator.demo_user_salesman')

        # Both users' contacts roll up to the same commercial partner = company.
        self.assertEqual(store_owner.partner_id.commercial_partner_id, company)
        self.assertEqual(salesman.partner_id.commercial_partner_id, company)
        self.assertEqual(
            store_owner.partner_id.commercial_partner_id,
            salesman.partner_id.commercial_partner_id,
            "Demo B2B users must share one commercial_partner_id (the company)",
        )

    def test_demo_coffin_option_prices(self):
        # price_extra was registered onto the auto-created PTAVs via xmlids.
        plywood = self.env.ref('funedistri_coffin_configurator.ptav_wood_plywood')
        gold = self.env.ref('funedistri_coffin_configurator.ptav_handles_gold')
        oak = self.env.ref('funedistri_coffin_configurator.ptav_wood_oak')

        self.assertEqual(plywood.price_extra, 120.0)
        self.assertEqual(gold.price_extra, 80.0)
        self.assertEqual(oak.price_extra, 0.0, "Base option stays +0")

    def test_demo_coffin_uses_no_variant_attributes(self):
        # The whole point: no SKU explosion — attributes are 'no_variant'.
        coffin = self.env.ref('funedistri_coffin_configurator.coffin_demo')
        for line in coffin.attribute_line_ids:
            self.assertEqual(line.attribute_id.create_variant, 'no_variant')
