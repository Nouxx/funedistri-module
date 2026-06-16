# -*- coding: utf-8 -*-
"""Shared test fixtures — a self-contained configurable coffin + B2B users.

Tests never depend on the dev seed (the main module must not depend on it). This
mixin builds, in ``setUpClass``, the minimum the tests need:
  - a published configurable coffin (``product.template``) with two priced
    ``no_variant`` attributes (Bois image, Poignées select);
  - one customer company with two portal users under it (a Store owner + a
    Salesman) sharing one commercial_partner_id and carrying the right
    ``b2b_role`` → security group.

Mix it BEFORE the Odoo base case so its ``setUpClass`` runs first:
    class TestX(CoffinFixtureMixin, HttpCase):
"""

from odoo.fields import Command

# Login (== password) for the two test users.
SALESMAN_LOGIN = 'tc_salesman'
STORE_OWNER_LOGIN = 'tc_store_owner'


class CoffinFixtureMixin:
    """Provides a coffin catalog + B2B users as class attributes:
    ``coffin``, ``coffin_variant``, ``company``, ``salesman``, ``store_owner``."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        env = cls.env
        Attr = env['product.attribute']
        Value = env['product.attribute.value']

        attr_wood = Attr.create({
            'name': 'Bois', 'display_type': 'image', 'create_variant': 'no_variant',
        })
        val_oak = Value.create({
            'name': 'Chêne', 'attribute_id': attr_wood.id, 'sequence': 10})
        val_plywood = Value.create({
            'name': 'Contreplaqué', 'attribute_id': attr_wood.id, 'sequence': 20})

        attr_handles = Attr.create({
            'name': 'Poignées', 'display_type': 'select', 'create_variant': 'no_variant',
        })
        val_handles_std = Value.create({
            'name': 'Standard', 'attribute_id': attr_handles.id, 'sequence': 10})
        val_handles_gold = Value.create({
            'name': 'Dorées', 'attribute_id': attr_handles.id, 'sequence': 20})

        coffin = env['product.template'].create({
            'name': 'Cercueil configurable (test)',
            'type': 'consu', 'sale_ok': True,
            'list_price': 600.0, 'is_published': True,
            'attribute_line_ids': [
                Command.create({
                    'attribute_id': attr_wood.id,
                    'value_ids': [Command.set([val_oak.id, val_plywood.id])],
                }),
                Command.create({
                    'attribute_id': attr_handles.id,
                    'value_ids': [Command.set([val_handles_std.id, val_handles_gold.id])],
                }),
            ],
        })

        def ptav(value):
            return coffin.attribute_line_ids.product_template_value_ids.filtered(
                lambda p: p.product_attribute_value_id == value)

        # Per-option prices on the auto-created PTAVs (base options stay +0).
        ptav(val_plywood).price_extra = 120.0
        ptav(val_handles_gold).price_extra = 80.0

        address = {
            'street': '1 rue du Test', 'city': 'Nantes', 'zip': '44000',
            'country_id': env.ref('base.fr').id,
        }
        company = env['res.partner'].create({
            'name': 'Test PF Company', 'is_company': True,
            'email': 'contact@test-pf.example.com', **address,
        })
        portal = env.ref('base.group_portal').id
        # phone is required for a complete billing address (else checkout would
        # redirect to complete it before showing the delivery selection).
        store_owner = env['res.users'].create({
            'name': 'Test Store Owner', 'login': STORE_OWNER_LOGIN,
            'password': STORE_OWNER_LOGIN,
            'group_ids': [Command.set([portal])],
            'parent_id': company.id, 'b2b_role': 'store_owner',
            'email': 'store.owner@test-pf.example.com', 'phone': '+33240000011',
            **address,
        })
        salesman = env['res.users'].create({
            'name': 'Test Salesman', 'login': SALESMAN_LOGIN,
            'password': SALESMAN_LOGIN,
            'group_ids': [Command.set([portal])],
            'parent_id': company.id, 'b2b_role': 'salesman',
            'email': 'salesman@test-pf.example.com', 'phone': '+33240000012',
            **address,
        })

        # An Owner-defined delivery address for the company (Step 5) + a rogue
        # address NOT belonging to the company (to assert it can't be selected).
        # NB: a delivery address must be COMPLETE for native checkout
        # (_check_delivery_address requires name, email, phone + the address
        # fields), else checkout would redirect to edit it.
        delivery_addr = env['res.partner'].create({
            'name': 'Funérarium Test', 'parent_id': company.id, 'type': 'delivery',
            'email': 'funerarium@test-pf.example.com', 'phone': '+33240000099',
            **address,
        })
        invoice_addr = env['res.partner'].create({
            'name': 'Compta Test', 'parent_id': company.id, 'type': 'invoice',
            'email': 'compta@test-pf.example.com', 'phone': '+33240000098',
            **address,
        })
        rogue_addr = env['res.partner'].create({
            'name': 'Rogue Address', 'type': 'delivery',
            'street': '99 rue Pirate', 'city': 'Paris', 'zip': '75001',
            'country_id': env.ref('base.fr').id,
        })

        cls.coffin = coffin
        cls.coffin_variant = coffin.product_variant_id
        cls.company = company
        cls.store_owner = store_owner
        cls.salesman = salesman
        cls.delivery_addr = delivery_addr
        cls.invoice_addr = invoice_addr
        cls.rogue_addr = rogue_addr
