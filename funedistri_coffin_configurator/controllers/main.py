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
from odoo.exceptions import ValidationError
from odoo.http import request, route

from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.addons.website_sale.controllers.cart import Cart
from odoo.addons.website_sale.controllers.delivery import Delivery
from odoo.addons.sale.controllers.portal import CustomerPortal

# The placeholder string the masked delivery JSON routes return instead of any
# amount. Mirrors the QWeb "Prix masqué" placeholder so the cart summary, were it
# ever shown, reads the same. Kept here (not a template) because these are JSON
# routes returning pre-rendered HTML fragments for the amount cells.
_MASKED_AMOUNT_HTML = '<span class="text-muted fst-italic coffin-price-masked">Prix masqué</span>'

from odoo.addons.funedistri_coffin_configurator.models.sale_order_line import (
    COFFIN_CONFIG_FIELDS,
)

# xmlid of the hidden "no prices" group. The render-side masking (QWeb) keys off
# this via the `groups` attribute; the JSON-route masking below keys off it via
# has_group on the CURRENT user — both are "the viewer IS the salesman" checks
# (ADR-0001). Async/document renders (email, PDF, portal order detail) instead
# key off the order partner's role — that is Step 7.
SALESMAN_GROUP = 'funedistri_coffin_configurator.coffin_salesman_group'


def _viewer_is_salesman():
    """True when the user making THIS request is a price-blind Salesman.

    Safe for public/no-session requests: has_group on the public user simply
    returns False, so the shop stays priced for anonymous browsing.
    """
    return request.env.user.has_group(SALESMAN_GROUP)


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

        # Data-integrity gate (Step 4): enforce required-when reveal rules now,
        # at submit. The JS reveal is UX only; a Salesman builds blind, so a
        # missing required field (e.g. death date when engraving = yes) must be
        # refused server-side before the Order becomes Pending.
        order_sudo.order_line._validate_reveal_rules()

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

    @route('/coffin/cart/line/save', type='jsonrpc', auth='user', website=True)
    def coffin_save_line_field(self, line_id, field, value, **kw):
        """Persist one custom config field (death date / engraving / …) on a line.

        Called by the cart-page JS when a field changes. Security: the line must
        belong to the CURRENT user's cart, so a user can't write fields on someone
        else's order. The ≤20-char constraint fires on write; we translate the
        error into a message the JS shows inline.
        """
        # Whitelist the field name — never write an arbitrary field from the web.
        allowed = {f['name'] for f in COFFIN_CONFIG_FIELDS}
        if field not in allowed:
            return {'error': "Champ inconnu."}

        cart = request.cart
        line = cart.order_line.filtered(lambda l: l.id == int(line_id))
        if not line:
            return {'error': "Ligne introuvable."}

        try:
            # Savepoint + flush so the ≤20-char constraint runs HERE and a bad
            # write is rolled back. Without the savepoint, catching the error and
            # returning normally would still COMMIT the invalid value.
            with request.env.cr.savepoint():
                # Empty string -> clear the field (False); Date/Char take the rest.
                line.write({field: value or False})
                line.flush_recordset()
        except ValidationError as e:
            return {'error': e.args[0] if e.args else "Valeur invalide."}
        return {'ok': True}


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


class CoffinCart(Cart):
    """Step 6 — strip the real money out of the cart JSON routes for a Salesman.

    The QWeb masking (views/price_visibility_templates.xml) hides prices in the
    rendered HTML — including the HTML fragments these routes return (cart_lines,
    totals), since those go through the same masked templates. But the routes
    ALSO return RAW numbers as plain JSON keys, which no template touches:

      - ``/shop/cart/update`` -> ``amount`` (order total) and ``minor_amount``.
      - ``/shop/cart/add``    -> ``notification_info.lines[].price_total`` and
                                 ``tracking_info[].price`` / ``discount``.

    ADR-0001's guardrail is that the server must NEVER emit the real number to a
    Salesman, not even in JSON. So we call super() and zero those keys for a
    Salesman. We zero rather than delete: the frontend JS expects the keys to
    exist; the displayed total is masked in the HTML anyway, so a 0 here is
    harmless and never reveals the real figure.

    Scope note (ADR-0001): this covers the main cart/checkout JSON surface, not
    every price-bearing route (e.g. variant-price recompute). Masking is
    practical, not adversary-proof — residual leakage via crafted requests is
    accepted for this non-adversarial B2B role.
    """

    def update_cart(self, line_id, quantity, product_id=None, **kwargs):
        values = super().update_cart(
            line_id, quantity, product_id=product_id, **kwargs
        )
        if _viewer_is_salesman():
            # Order total + its minor-units (cents) form. Never hand the real
            # number to a price-blind Salesman.
            values['amount'] = 0.0
            values['minor_amount'] = 0
        return values

    def _get_cart_notification_information(self, order, added_qty_per_line):
        # The "added to cart" toast lists each added line's price_total. Zero it
        # for a Salesman so the toast carries no money.
        info = super()._get_cart_notification_information(order, added_qty_per_line)
        if _viewer_is_salesman():
            for line in info.get('lines', []):
                line['price_total'] = 0.0
        return info

    def _get_tracking_information(self, order_sudo, line_ids):
        # Analytics payload (datalayer) also carries unit price + discount. Zero
        # them for a Salesman — same no-number-emitted rule.
        info = super()._get_tracking_information(order_sudo, line_ids)
        if _viewer_is_salesman():
            for item in info:
                item['price'] = 0.0
                item['discount'] = 0.0
        return info


class CoffinDelivery(Delivery):
    """Step 6 — strip amounts out of the delivery-step JSON routes for a Salesman.

    The checkout (address) page lets the user pick a delivery method; two JSON
    routes feed it money that QWeb masking can't reach:

      - ``/shop/set_delivery_method`` -> ``_order_summary_values`` returns the
        order's delivery/untaxed/tax/total amounts (as rendered HTML).
      - ``/shop/get_delivery_rate``   -> returns the carrier ``price`` and its
        rendered ``amount_delivery``.

    ADR-0001's guardrail: the server must NEVER emit the real number to a Salesman,
    not even in JSON. So we replace those amounts with the "Prix masqué"
    placeholder (and zero the raw ``price``). We keep ``success`` truthy so the
    delivery method still counts as selectable — otherwise the native JS would
    disable the carrier and, with it, the "Confirm" button.

    NB: even with these masked, the native checkout JS would still try to write
    the values into the (removed) totals table; ``coffin_checkout_mask.js`` guards
    that crash. The two fixes are complementary: this one stops the leak, the JS
    one stops the throw.
    """

    def _order_summary_values(self, order, **kwargs):
        values = super()._order_summary_values(order, **kwargs)
        if _viewer_is_salesman():
            for key in ('amount_delivery', 'amount_untaxed', 'amount_tax',
                        'amount_total'):
                if key in values:
                    values[key] = _MASKED_AMOUNT_HTML
        return values

    def shop_get_delivery_rate(self, dm_id):
        rate = super().shop_get_delivery_rate(dm_id)
        if _viewer_is_salesman() and isinstance(rate, dict):
            # Never hand the carrier price to a price-blind Salesman. Keep the
            # rate "successful" so the method stays selectable; only the figure
            # is suppressed.
            if 'price' in rate:
                rate['price'] = 0.0
            if 'amount_delivery' in rate:
                rate['amount_delivery'] = _MASKED_AMOUNT_HTML
            # Force the "Free" wording off so we don't imply a zero price; the
            # placeholder already conveys "hidden".
            rate['is_free_delivery'] = False
        return rate
