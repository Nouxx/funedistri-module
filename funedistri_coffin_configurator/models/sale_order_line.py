# -*- coding: utf-8 -*-
"""Custom configuration fields captured per Configured coffin (order line).

These are the "dev-defined but generic" fields from CLAUDE.md: each is a real
column in code, each is OPTIONAL, and whether one is shown/required is driven by
coffin.config.rule (Step 4), not hard-coded here. Adding a brand-new field type
is a dev touch; wiring an existing field to a trigger is data-only.

A Configured coffin = one sale.order.line, so these live on sale.order.line.
"""

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

# Single source of truth for the ≤20-char engraving rule. Imported by the rule
# validation too, so the number lives in exactly one place.
ENGRAVING_MAX_LEN = 20

# The custom config fields a buyer can fill on a Configured coffin, with how to
# render them. 'maxlength' is the browser hint for engraving (server enforces it
# too). Adding a new field = add the column above + an entry here (+ to the rule
# Selection). Keep aligned with coffin_config_rule.TARGET_FIELD_SELECTION.
COFFIN_CONFIG_FIELDS = [
    {'name': 'death_date', 'label': "Date de décès", 'widget': 'date'},
    {'name': 'delivery_date', 'label': "Date de livraison souhaitée", 'widget': 'date'},
    {'name': 'engraving_text', 'label': "Texte de gravure", 'widget': 'char',
     'maxlength': ENGRAVING_MAX_LEN},
]


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    # Deceased's date of death — engraved on the coffin plate. Optional; a
    # reveal rule may make it required when engraving is chosen.
    death_date = fields.Date(
        string="Date de décès",
        help="Date de décès du défunt, gravée sur la plaque du cercueil.",
    )

    # Deadline by which the Salesman needs delivery. Logistics only, not engraved.
    delivery_date = fields.Date(
        string="Date de livraison souhaitée",
        help="Date limite à laquelle la commande doit être livrée.",
    )

    # Free text engraved on the plate. ≤20 chars (constraint below — native
    # custom-value text has no length validation).
    engraving_text = fields.Char(
        string="Texte de gravure",
        help="Texte gravé sur la plaque (20 caractères maximum).",
    )

    @api.constrains('engraving_text')
    def _check_engraving_text_length(self):
        # Data integrity, not UX: even if the JS/length attribute is bypassed,
        # the server refuses an over-long engraving. Empty stays valid (optional).
        # Always-on (cheap, single-field) — unlike required-when, which is checked
        # at submit so a half-built cart line isn't rejected mid-edit.
        for line in self:
            if line.engraving_text and len(line.engraving_text) > ENGRAVING_MAX_LEN:
                raise ValidationError(_(
                    "Le texte de gravure ne peut pas dépasser %s caractères "
                    "(actuellement %s).",
                    ENGRAVING_MAX_LEN, len(line.engraving_text),
                ))

    def _selected_trigger_values(self):
        """The GLOBAL attribute values currently selected on this line.

        The line stores per-coffin PTAVs in product_no_variant_attribute_value_ids;
        a reveal rule keys on the global product.attribute.value, so we map each
        selected PTAV back to its global value.
        """
        self.ensure_one()
        return self.product_no_variant_attribute_value_ids.product_attribute_value_id

    def _validate_reveal_rules(self):
        """Enforce required-when reveal rules (the server is the truth).

        For each line, find the rules triggered by its selected values that are
        marked required_when, and refuse if the target field is empty. This is
        the data-integrity gate: a Salesman builds blind to price and the JS is
        only UX, so a missing required field must be caught here — called at
        submit (see the /shop/submit_order controller).
        """
        Rule = self.env['coffin.config.rule'].sudo()
        for line in self:
            triggers = line._selected_trigger_values()
            if not triggers:
                continue
            rules = Rule.search([
                ('trigger_value_id', 'in', triggers.ids),
                ('required_when', '=', True),
            ])
            for rule in rules:
                if not line[rule.target_field]:
                    label = dict(rule._fields['target_field'].selection)[rule.target_field]
                    raise ValidationError(_(
                        "Le champ « %s » est obligatoire pour l'option choisie "
                        "(%s).",
                        label, rule.trigger_value_id.display_name,
                    ))

    def _coffin_config_field_specs(self):
        """Render-ready spec for the custom fields on this line (the cart UI).

        For each custom field we compute, FROM the rules (single source of
        truth), which trigger values reveal it and whether it's then required —
        restricted to the values this coffin actually offers. The cart template
        renders these into data-* attributes and a small JS reveals the field
        when one of its trigger values is selected. A field with no rule has no
        triggers -> always shown (e.g. delivery date).
        """
        self.ensure_one()
        Rule = self.env['coffin.config.rule'].sudo()
        # Global attribute values this coffin offers, and which are selected now.
        offered = self.product_template_id.attribute_line_ids.value_ids
        selected = self._selected_trigger_values()

        specs = []
        for fdef in COFFIN_CONFIG_FIELDS:
            rules = Rule.search([('target_field', '=', fdef['name'])]).filtered(
                lambda r: r.trigger_value_id in offered
            )
            triggers = rules.trigger_value_id
            spec = dict(fdef)
            spec['trigger_value_ids'] = triggers.ids
            spec['required'] = any(rules.filtered('required_when'))
            # Server-side initial reveal state (JS re-applies on the client too).
            spec['revealed'] = (not triggers) or bool(triggers & selected)
            value = self[fdef['name']]
            # Dates -> ISO string for the <input type="date"> value attribute.
            if fdef['widget'] == 'date' and value:
                value = fields.Date.to_string(value)
            spec['value'] = value or ''
            specs.append(spec)
        return specs
