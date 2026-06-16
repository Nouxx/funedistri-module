# -*- coding: utf-8 -*-
"""Address lock — checkout readiness when a company address is missing (ADR 0005).

When a B2B user's company lacks a required address type (no Invoice, or no Delivery
for a deliverable cart), checkout cannot complete. Rather than bounce the user back
to the cart, we let the checkout page render with the "continue" button DISABLED
(native `_is_cart_ready()` already drives that button) plus an explanatory notice —
clearer than a silent redirect. The Owner must define the missing address.
"""

from odoo import models
from odoo.http import request


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

    def _is_cart_ready(self):
        # Disable the checkout "continue" button for a B2B order whose company is
        # missing a required address type (block-on-missing) — they cannot proceed
        # until the Owner defines it.
        ready = super()._is_cart_ready()
        if (
            ready
            and request
            and not request.env.user._is_public()
            and request.env.user._coffin_is_b2b_user()
            and self._coffin_addresses_blocked()
        ):
            return False
        return ready
