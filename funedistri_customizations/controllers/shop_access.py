# -*- coding: utf-8 -*-
"""Shop access — only CONFIGURED B2B users (or staff) may reach the shop.

Step 3's native gate (`ecommerce_access='logged_in'`) only tells public from
logged-in; it lets ANY logged-in user — including an ORPHAN portal user with no
company/role — into the shop. New rule: a logged-in user must be a configured
B2B user (in a coffin role group) to shop.

WHY NOT just override `has_ecommerce_access()`?
Native shop/cart/product controllers, when that returns False, redirect to
`/web/login`. That is correct for the PUBLIC user (they log in and pass) but a
logged-in-yet-denied orphan would be sent to login, bounced back (already authed),
and loop. So instead we guard the shop entry routes here and send a denied
authenticated user to their portal home (`/my`) — no loop, clear destination.

Native has no group-granular shop restriction, so this small per-entry guard is
the minimal correct hook.
"""

from odoo.http import request

from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.addons.website_sale.controllers.cart import Cart


def _coffin_shop_denied():
    """True when the CURRENT user is logged in but may not shop (an orphan).

    Delegates the decision to res.users._coffin_can_shop(). Public users return
    "can shop" here (not denied) so they fall through to the native login gate
    (Step 3) rather than being sent to /my.
    """
    return not request.env.user._coffin_can_shop()


class CoffinShopAccess(WebsiteSale):

    def shop(self, page=0, category=None, search='', min_price=0.0,
             max_price=0.0, tags='', **post):
        if _coffin_shop_denied():
            return request.redirect('/my')
        return super().shop(page=page, category=category, search=search,
                             min_price=min_price, max_price=max_price,
                             tags=tags, **post)

    def product(self, product, category=None, pricelist=None, **kwargs):
        if _coffin_shop_denied():
            return request.redirect('/my')
        return super().product(product, category=category, pricelist=pricelist,
                                **kwargs)


class CoffinCartAccess(Cart):

    def cart(self, id=None, access_token=None, revive_method='', **post):
        if _coffin_shop_denied():
            return request.redirect('/my')
        return super().cart(id=id, access_token=access_token,
                             revive_method=revive_method, **post)
