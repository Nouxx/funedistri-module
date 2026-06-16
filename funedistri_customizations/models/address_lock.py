# -*- coding: utf-8 -*-
"""Address lock — checkout readiness when a company address is missing (ADR 0005).

When a B2B user's company lacks a required address type (no Invoice, or no Delivery
for a deliverable cart), checkout cannot complete. The user can still go from the
cart to the ADDRESS step, but the "continue" button THERE is disabled with a notice
(see views/address_lock_templates.xml — keyed on these helpers + the current step,
NOT on `_is_cart_ready`, which also gates the cart's own Checkout button). The Owner
must define the missing address.
"""

from odoo import models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _coffin_required_address_types(self):
        self.ensure_one()
        types = ['invoice']                      # billing always required
        if not self.only_services:
            types.append('delivery')             # shipping for deliverable carts
        return types

    def _coffin_company_has_address(self, addr_type):
        """Whether the order's company has at least one child contact of this type."""
        self.ensure_one()
        commercial = self.partner_id.commercial_partner_id
        return bool(self.env['res.partner'].sudo().search_count([
            ('id', 'child_of', commercial.id),
            ('type', '=', addr_type),
        ]))

    def _coffin_addresses_blocked(self):
        """True when a B2B order's company lacks a required address type."""
        self.ensure_one()
        return any(not self._coffin_company_has_address(t)
                   for t in self._coffin_required_address_types())
