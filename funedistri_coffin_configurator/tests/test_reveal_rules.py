# -*- coding: utf-8 -*-
"""Step 4.3 — server-truth tests for conditional-reveal rules.

The two invariants the server must guarantee (JS is UX only):
  1. required-when: if a rule's trigger value is selected on a line and the rule
     is required_when, the target field must be filled — else submit is refused.
  2. the ≤20-char engraving constraint rejects an over-long text.
"""

from odoo.exceptions import ValidationError
from odoo.tests import HttpCase, TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestRevealRules(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.coffin = cls.env.ref('funedistri_coffin_configurator.coffin_demo')
        yes_value = cls.env.ref('funedistri_coffin_configurator.attr_engraving_yes')
        # The per-coffin PTAV for Gravure = Oui (what a line actually stores).
        cls.yes_ptav = cls.coffin.attribute_line_ids.product_template_value_ids.filtered(
            lambda p: p.product_attribute_value_id == yes_value
        )
        cls.partner = cls.env['res.partner'].create({'name': 'Rule Test Partner'})

    def _make_line(self, **vals):
        order = self.env['sale.order'].create({'partner_id': self.partner.id})
        return self.env['sale.order.line'].create({
            'order_id': order.id,
            'product_id': self.coffin.product_variant_id.id,
            'product_no_variant_attribute_value_ids': [(6, 0, self.yes_ptav.ids)],
            **vals,
        })

    def test_required_when_blocks_missing_target(self):
        # Gravure = Oui selected, but death_date + engraving_text empty.
        line = self._make_line()
        with self.assertRaises(ValidationError):
            line._validate_reveal_rules()

    def test_required_when_passes_when_filled(self):
        line = self._make_line(death_date='2026-01-01', engraving_text='Jean Dupont')
        # Should not raise.
        line._validate_reveal_rules()

    def test_no_trigger_no_requirement(self):
        # Without the Oui value selected, the required-when rules don't apply.
        order = self.env['sale.order'].create({'partner_id': self.partner.id})
        line = self.env['sale.order.line'].create({
            'order_id': order.id,
            'product_id': self.coffin.product_variant_id.id,
        })
        line._validate_reveal_rules()  # no raise

    def test_engraving_too_long_rejected(self):
        with self.assertRaises(ValidationError):
            self._make_line(engraving_text='X' * 21)

    def test_engraving_within_limit_ok(self):
        line = self._make_line(death_date='2026-01-01', engraving_text='X' * 20)
        self.assertEqual(len(line.engraving_text), 20)


@tagged('post_install', '-at_install')
class TestRevealRulesWeb(HttpCase):
    """The cart-page capture: fields render, and the save route persists/validates."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.coffin = cls.env.ref('funedistri_coffin_configurator.coffin_demo')
        yes_value = cls.env.ref('funedistri_coffin_configurator.attr_engraving_yes')
        cls.yes_ptav = cls.coffin.attribute_line_ids.product_template_value_ids.filtered(
            lambda p: p.product_attribute_value_id == yes_value
        )
        cls.user = cls.env['res.users'].create({
            'name': 'Web Rule User',
            'login': 'web_rule_user',
            'password': 'web_rule_user',
            'group_ids': [(6, 0, [cls.env.ref('base.group_portal').id])],
            'email': 'web_rule_user@example.com',
            'phone': '+33100000000',
            'street': '1 rue du Test', 'city': 'Paris', 'zip': '75001',
            'country_id': cls.env.ref('base.fr').id,
        })

    def test_cart_renders_fields_and_save_route(self):
        self.authenticate('web_rule_user', 'web_rule_user')
        # Add the coffin with Gravure = Oui selected.
        self.make_jsonrpc_request('/shop/cart/add', {
            'product_template_id': self.coffin.id,
            'product_id': self.coffin.product_variant_id.id,
            'quantity': 1,
            'no_variant_attribute_value_ids': self.yes_ptav.ids,
        })
        order = self.env['sale.order'].search(
            [('partner_id', '=', self.user.partner_id.id)], limit=1)
        line = order.order_line[:1]
        self.assertTrue(line.product_no_variant_attribute_value_ids,
                        "Gravure = Oui should be recorded on the line")

        # The cart page renders the config-field block with the required marker.
        cart_html = self.url_open('/shop/cart').text
        self.assertIn('o_coffin_config_fields', cart_html)
        self.assertIn('Texte de gravure', cart_html)

        # Save route rejects an over-long engraving...
        res = self.make_jsonrpc_request('/coffin/cart/line/save', {
            'line_id': line.id, 'field': 'engraving_text', 'value': 'X' * 21,
        })
        self.assertIn('error', res)
        self.assertFalse(line.engraving_text)

        # ...and persists a valid one.
        res = self.make_jsonrpc_request('/coffin/cart/line/save', {
            'line_id': line.id, 'field': 'engraving_text', 'value': 'Jean Dupont',
        })
        self.assertTrue(res.get('ok'))
        line.invalidate_recordset()
        self.assertEqual(line.engraving_text, 'Jean Dupont')
