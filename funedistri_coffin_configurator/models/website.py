# -*- coding: utf-8 -*-
"""Stop a submitted Pending Order from being resurrected as the shopping cart.

Odoo's cart resolver (``website._get_and_cache_current_cart``) does two things
that bite our flow A:
  - it reuses the order whose id is in the session, and
  - for a logged-in user with NO session cart, it searches for an "abandoned
    cart" = any ``state='draft'`` order of that partner and revives it.

Our submitted Order stays ``draft`` (= Pending). So after submit — even though
the controller calls ``sale_reset()`` to detach the session — the very next page
load finds that draft and revives it as the cart, making it look like checkout
never emptied the cart.

A submitted Order is NOT a cart. We wrap the resolver: if it ever hands back an
order flagged ``coffin_is_submitted``, we reset and return an empty cart instead.
"""

from odoo import models
from odoo.http import request

from odoo.addons.website_sale.models.website import CART_SESSION_CACHE_KEY


class Website(models.Model):
    _inherit = 'website'

    def _get_and_cache_current_cart(self):
        cart = super()._get_and_cache_current_cart()
        if cart and cart.coffin_is_submitted:
            # Never use a submitted Pending Order as the live cart.
            self.sale_reset()
            if request and not self.env.user._is_public():
                # Mirror Odoo's "logged-in but no cart" marker (id stored as
                # False) so the abandoned-cart search doesn't re-find this same
                # order on every subsequent request.
                request.session[CART_SESSION_CACHE_KEY] = False
            return self.env['sale.order'].sudo()
        return cart
