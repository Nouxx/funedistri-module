# -*- coding: utf-8 -*-
"""Website checkout overrides for the coffin configurator.

Step 1 (tracer spine) adds ONE route: ``/shop/submit_order``. It replaces
Odoo's online-payment final step with our "flow A" — submit creates no payment,
it just hands the existing cart to the Owner as a *Pending* Order.

Key fact about Odoo's e-commerce: the cart a B2B user fills IS already a
``sale.order`` in the ``draft`` state. So we do NOT create anything on submit —
we simply *finalise* that draft: detach it from the live cart session (so the
user starts fresh next time and the order shows up in their portal history) and
send them to the confirmation page. The Owner later turns it into a real Order
with ``action_confirm()`` (``draft`` -> ``sale``); see CLAUDE.md.

We inherit the stock ``WebsiteSale`` controller so we can reuse its cart/address
validation helper instead of re-implementing it.
"""

from odoo import http
from odoo.http import request, route

from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.addons.sale.controllers.portal import CustomerPortal


class CoffinWebsiteSale(WebsiteSale):

    # auth='user': only logged-in B2B users reach the protected configurator,
    # so submitting an order always requires a session (never the public user).
    # methods=['POST']: this mutates state (finalises an order), so it must be a
    # POST behind Odoo's CSRF token, not a GET that a stray link could trigger.
    @route('/shop/submit_order', type='http', auth='user', website=True,
           methods=['POST'])
    def shop_submit_order(self, **post):
        """Finalise the current cart as a Pending (draft) Order — no payment.

        Mirrors the tail of Odoo's ``/shop/payment/validate`` for a zero-payment
        order, MINUS the ``_validate_order()`` call: we deliberately leave the
        order in ``draft`` so it stays *Pending* until the Owner validates it.
        """
        order_sudo = request.cart

        # Reuse the native guard: bail out (redirect) if the cart is empty,
        # not in draft, or missing required addresses. Returns a redirect
        # response when something is off, else None.
        if redirection := self._check_cart_and_addresses(order_sudo):
            return redirection

        # Make sure totals/taxes are up to date before we hand the order over.
        order_sudo._recompute_cart()

        # Mark this draft as a SUBMITTED Order (Pending), not a live cart. This
        # is what lets the portal list it as Pending without also showing carts.
        order_sudo.coffin_is_submitted = True

        # Remember which order to show on the confirmation page. The confirmation
        # route reads this exact session key; the live cart key is separate.
        request.session['sale_last_order_id'] = order_sudo.id

        # Detach the order from the live cart session (pops 'sale_order_id' &
        # friends). The order itself is untouched and stays in 'draft' = Pending;
        # the user's next visit starts a brand-new empty cart.
        request.website.sale_reset()

        # Land on the shared confirmation page (FR wording handled in 1.4).
        return request.redirect('/shop/confirmation')


class CoffinCustomerPortal(CustomerPortal):
    """Make submitted Pending Orders visible in the B2B user's portal.

    Native ``/my/orders`` lists only confirmed Orders (``state='sale'``). Our
    Pending Orders sit in ``draft``, so we widen the domain to ALSO include
    drafts that were actually submitted (``coffin_is_submitted=True``) — never
    plain shopping carts (draft + not submitted).
    """

    def _prepare_orders_domain(self, partner):
        # Start from the native domain (confirmed Orders for this company), then
        # OR-in our submitted drafts. We rebuild rather than super()-extend
        # because the native domain hard-codes state='sale'.
        return [
            ('partner_id', 'child_of', [partner.commercial_partner_id.id]),
            '|',
                ('state', '=', 'sale'),
                '&', ('state', '=', 'draft'), ('coffin_is_submitted', '=', True),
        ]
