# -*- coding: utf-8 -*-
"""One-level conditional-reveal rules — the single source of truth (ADR-0002).

A rule says: "when the buyer picks TRIGGER, reveal TARGET field (and optionally
require it)." Three readers consume the SAME rows, so nothing is duplicated:
  1. the product page renders them into DOM data-* attributes,
  2. a small JS snippet shows/hides/disables fields (UX only),
  3. the server reads them to validate required-when (the truth).

Trigger = a native attribute VALUE (e.g. Gravure: Oui), per the Step 4 decision
to model yes/no options as native attributes rather than custom fields. We key on
the global product.attribute.value (not the per-coffin PTAV) so one rule applies
wherever that value is offered.
"""

from odoo import fields, models

# The custom line fields a rule may target. Keep in sync with the fields defined
# on sale.order.line — adding a new targetable field = add it here + on the line.
TARGET_FIELD_SELECTION = [
    ('death_date', "Date de décès"),
    ('delivery_date', "Date de livraison souhaitée"),
    ('engraving_text', "Texte de gravure"),
]


class CoffinConfigRule(models.Model):
    _name = 'coffin.config.rule'
    _description = "Coffin configurator conditional-reveal rule"

    # The choice that activates this rule. A global attribute value so the rule
    # holds across every coffin that offers it (we match it against each order
    # line's selected no-variant values).
    trigger_value_id = fields.Many2one(
        comodel_name='product.attribute.value',
        string="Trigger option value",
        required=True,
        ondelete='cascade',
        help="When the buyer selects this option value, the target field is "
             "revealed (and required if 'Required when triggered' is set).",
    )

    # Which custom line field to reveal/require. A Selection (not a free relation)
    # because the fields live in code on sale.order.line.
    target_field = fields.Selection(
        selection=TARGET_FIELD_SELECTION,
        string="Field to reveal",
        required=True,
    )

    # If True the target must be filled when the trigger is active — enforced
    # server-side (data integrity, e.g. death date when engraving = yes).
    required_when = fields.Boolean(
        string="Required when triggered",
        default=False,
        help="If set, the revealed field becomes mandatory once the trigger is "
             "selected. Enforced on the server, not only in the browser.",
    )

    _sql_constraints = [
        # One rule per (trigger, target): a value either reveals a field or not.
        ('trigger_target_uniq',
         'unique(trigger_value_id, target_field)',
         "A rule already exists for this trigger value and target field."),
    ]
