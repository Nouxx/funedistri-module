# -*- coding: utf-8 -*-
"""Shared test fixtures — a self-contained configurable coffin + B2B users.

WHY THIS EXISTS
The old test suite leaned on the demo seed (``env.ref('..coffin_demo')`` etc).
That seed was retired (it now lives in the local-only ``funedistri_dev_seed``
module, which the main module must NOT depend on). Tests should never depend on
seed/demo data anyway: they build exactly the records they assert on, so they
stay green whatever the seed contains.

This mixin builds, in ``setUpClass``, the minimum the tests need:
  - a configurable coffin (``product.template``) with three ``no_variant``
    attributes: Bois (image, priced), Poignées (select, priced) and Gravure
    (radio) — the last is the reveal-rule TRIGGER;
  - per-option prices on the auto-created PTAVs (Contreplaqué +120, Dorées +80);
  - two reveal rules: Gravure = Oui requires death_date AND engraving_text;
  - one customer company with two portal users under it (a Store owner and a
    Salesman), so they share one commercial_partner_id and carry the right
    ``b2b_role`` → security group.

Mix it BEFORE the Odoo base case so its ``setUpClass`` runs first:
    class TestX(CoffinFixtureMixin, HttpCase):
"""

from odoo.fields import Command

# Login (== password) for the two seeded test users. Constant across test
# classes is fine — each class runs in its own rolled-back transaction.
SALESMAN_LOGIN = 'tc_salesman'
STORE_OWNER_LOGIN = 'tc_store_owner'


class CoffinFixtureMixin:
    """Provides a coffin catalog + B2B users as class attributes.

    Sets on the class: ``coffin``, ``coffin_variant``, the priced PTAVs
    (``ptav_oak`` +0, ``ptav_plywood`` +120, ``ptav_gold`` +80), the Gravure=Oui
    value (``engraving_yes_value``) and its per-coffin PTAV (``engraving_yes_ptav``),
    the ``company``, and the two users (``salesman`` / ``store_owner``).
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._build_coffin_fixtures()

    @classmethod
    def _build_coffin_fixtures(cls):
        env = cls.env
        Attr = env['product.attribute']
        Value = env['product.attribute.value']

        # --- Options as native "no_variant" attributes (CLAUDE.md decision: the
        #     choice is captured on the order line, no SKU explosion). ---
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

        # Gravure = the reveal-rule TRIGGER. Unpriced; "Oui" reveals/requires the
        # death date + engraving text.
        attr_engraving = Attr.create({
            'name': 'Gravure', 'display_type': 'radio', 'create_variant': 'no_variant',
        })
        val_engraving_no = Value.create({
            'name': 'Non', 'attribute_id': attr_engraving.id, 'sequence': 10})
        val_engraving_yes = Value.create({
            'name': 'Oui', 'attribute_id': attr_engraving.id, 'sequence': 20})

        # --- The configurable coffin, wired to the three attributes. Creating
        #     the attribute LINES auto-creates one PTAV per offered value. ---
        coffin = env['product.template'].create({
            'name': 'Cercueil configurable (test)',
            'type': 'consu',
            'sale_ok': True,
            'list_price': 600.0,
            'is_published': True,
            'attribute_line_ids': [
                Command.create({
                    'attribute_id': attr_wood.id,
                    'value_ids': [Command.set([val_oak.id, val_plywood.id])],
                }),
                Command.create({
                    'attribute_id': attr_handles.id,
                    'value_ids': [Command.set([val_handles_std.id, val_handles_gold.id])],
                }),
                Command.create({
                    'attribute_id': attr_engraving.id,
                    'value_ids': [Command.set([val_engraving_no.id, val_engraving_yes.id])],
                }),
            ],
        })

        def ptav(value):
            """The per-coffin PTAV that wraps a global attribute value."""
            return coffin.attribute_line_ids.product_template_value_ids.filtered(
                lambda p: p.product_attribute_value_id == value
            )

        # Prices live on the PTAVs (base options stay +0).
        ptav(val_plywood).price_extra = 120.0
        ptav(val_handles_gold).price_extra = 80.0

        # --- Reveal rules: Gravure = Oui requires both custom fields. ---
        env['coffin.config.rule'].create([
            {'trigger_value_id': val_engraving_yes.id,
             'target_field': 'death_date', 'required_when': True},
            {'trigger_value_id': val_engraving_yes.id,
             'target_field': 'engraving_text', 'required_when': True},
        ])

        # --- One customer company + two portal users under it. Sharing parent_id
        #     gives them one commercial_partner_id (native company-scoped order
        #     visibility); setting b2b_role drops each into its hidden group. ---
        address = {
            'street': '1 rue du Test', 'city': 'Nantes', 'zip': '44000',
            'country_id': env.ref('base.fr').id,
        }
        company = env['res.partner'].create({
            'name': 'Test PF Company', 'is_company': True,
            'email': 'contact@test-pf.example.com', **address,
        })
        portal = env.ref('base.group_portal').id
        store_owner = env['res.users'].create({
            'name': 'Test Store Owner', 'login': STORE_OWNER_LOGIN,
            'password': STORE_OWNER_LOGIN,
            'group_ids': [Command.set([portal])],
            'parent_id': company.id, 'b2b_role': 'store_owner',
            'email': 'store.owner@test-pf.example.com', **address,
        })
        salesman = env['res.users'].create({
            'name': 'Test Salesman', 'login': SALESMAN_LOGIN,
            'password': SALESMAN_LOGIN,
            'group_ids': [Command.set([portal])],
            'parent_id': company.id, 'b2b_role': 'salesman',
            'email': 'salesman@test-pf.example.com', **address,
        })

        # --- Expose everything the tests assert on. ---
        cls.coffin = coffin
        cls.coffin_variant = coffin.product_variant_id
        cls.val_oak = val_oak
        cls.val_plywood = val_plywood
        cls.val_handles_gold = val_handles_gold
        cls.engraving_yes_value = val_engraving_yes
        cls.ptav_oak = ptav(val_oak)
        cls.ptav_plywood = ptav(val_plywood)
        cls.ptav_gold = ptav(val_handles_gold)
        cls.engraving_yes_ptav = ptav(val_engraving_yes)
        cls.company = company
        cls.store_owner = store_owner
        cls.salesman = salesman
