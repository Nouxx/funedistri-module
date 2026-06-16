# -*- coding: utf-8 -*-
"""Submit-order flow — keep the cart empty after an Order is placed.

(Shop-access denial for orphan users lives in controllers/shop_access.py — it
must redirect to the portal home, not deny via has_ecommerce_access, which would
bounce a logged-in user into a /web/login redirect loop.)
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
