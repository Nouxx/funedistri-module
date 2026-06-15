# -*- coding: utf-8 -*-
"""Submit-order flow — website routes (Step 1, tracer spine).

Two overrides of stock website_sale controllers:
  1. /shop/submit_order — replaces the online-payment step with our no-payment
     "Valider la commande": flags the current cart as a Pending Order + notifies
     the Owner, then lands on the confirmation page.
  2. the portal orders domain — so a submitted Pending Order (draft + submitted)
     shows in the B2B user's /my/orders, while live carts stay hidden.
"""

from odoo.http import request, route

from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.addons.sale.controllers.portal import CustomerPortal


class CoffinWebsiteSale(WebsiteSale):

    # auth='user': only logged-in users reach this (the configurator is gated from
    #   Step 3; even now, submitting needs a session, never the public user).
    # methods=['POST']: this mutates state, so it must be a CSRF-protected POST,
    #   not a GET a stray link could fire.
    @route('/shop/submit_order', type='http', auth='user', website=True,
           methods=['POST'])
    def shop_submit_order(self, **post):
        """Finalise the current cart as a Pending (draft) Order — no payment."""
        order_sudo = request.cart

        # Reuse Odoo's native guard: returns a redirect if the cart is empty, not
        # in draft, or missing required addresses; else None and we proceed.
        if redirection := self._check_cart_and_addresses(order_sudo):
            return redirection

        # Make sure totals/taxes are current before we hand the Order over.
        order_sudo._recompute_cart()

        # Flag it Pending + notify the Owner (activity + email). See the model.
        order_sudo._coffin_submit_as_pending()

        # The confirmation route reads this session key to know which Order to show.
        request.session['sale_last_order_id'] = order_sudo.id

        # Detach the Order from the live cart session: the Order itself is untouched
        # (still 'draft' = Pending) but the user's next visit starts a fresh cart.
        request.website.sale_reset()

        return request.redirect('/shop/confirmation')


class CoffinCustomerPortal(CustomerPortal):
    """Make submitted Pending Orders visible in the B2B user's portal list.

    Native /my/orders lists only confirmed Orders (state='sale'). Our Pending
    Orders sit in 'draft', so we widen the domain to ALSO include drafts that were
    actually submitted (coffin_is_submitted=True) — never plain carts.
    """

    def _prepare_orders_domain(self, partner):
        # Rebuild (rather than super-extend) because the native domain hard-codes
        # state='sale'. Company scoping via commercial_partner_id is native.
        return [
            ('partner_id', 'child_of', [partner.commercial_partner_id.id]),
            '|',
                ('state', '=', 'sale'),
                '&', ('state', '=', 'draft'), ('coffin_is_submitted', '=', True),
        ]
