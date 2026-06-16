# -*- coding: utf-8 -*-
"""Submit-order flow — keep the cart empty after an Order is placed.

Flow A keeps a submitted Pending Order in ``state='draft'`` (Pending = draft +
coffin_is_submitted). But native ``website_sale`` treats ANY draft order of the
logged-in partner as a resurrectable "abandoned cart": after we detach the cart
at submit (``sale_reset()`` pops the session key), the very next request searches
for a draft order by partner and finds the just-placed Pending Order — bringing it
back as the cart, so the cart never clears.

We override the cart resolver to drop a submitted Order: it is no longer a cart.
"""

from odoo import models


class Website(models.Model):
    _inherit = 'website'

    def _get_and_cache_current_cart(self):
        # Let native resolve the cart first (incl. its abandoned-cart search).
        cart = super()._get_and_cache_current_cart()
        # If what it found is a SUBMITTED Pending Order, it is not a cart anymore.
        # Forget it (clear the session keys) and hand back an empty order, so the
        # user starts a fresh cart. Plain draft carts (not submitted) are untouched.
        if cart and cart.coffin_is_submitted:
            self.sale_reset()
            return self.env['sale.order'].sudo()
        return cart
