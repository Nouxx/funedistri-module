# -*- coding: utf-8 -*-
"""Extensions to Odoo's ``sale.order`` for the coffin configurator."""

from odoo import fields, models


class SaleOrder(models.Model):
    # _inherit (not _name) = we EXTEND the existing sale.order model, adding a
    # field to it rather than creating a new model. This is Odoo's standard way
    # to bolt data onto a core model.
    _inherit = 'sale.order'

    # WHY this field exists:
    # In Odoo a shopping cart and a freshly-submitted Order are BOTH 'draft'
    # sale.orders — there is no native flag to tell them apart. Our flow A keeps
    # a submitted Order in 'draft' (= "Pending", awaiting the Owner's Validate),
    # so without a marker we could not list submitted Orders in the B2B user's
    # portal without also listing their abandoned carts.
    #
    # The submit controller flips this to True at submit time; the portal orders
    # domain then shows "draft AND submitted" Orders (the Pending ones) while
    # still hiding live carts. The Owner's Validate later moves state to 'sale'.
    coffin_is_submitted = fields.Boolean(
        string="Submitted (Pending validation)",
        default=False,
        copy=False,  # a duplicated order should start as a fresh, un-submitted cart
        help="Set when a B2B user submits this Order at checkout. Distinguishes "
             "a Pending Order (draft + submitted) from a live shopping cart "
             "(draft + not submitted).",
    )
