# -*- coding: utf-8 -*-
"""Price masking for the SALESMAN — the non-render surfaces (Step 4, ADR 0001).

The render-side masking (QWeb placeholder across shop/cart/checkout/portal-list)
lives in views/price_visibility_templates.xml. This file covers what QWeb can't:

  1. JSON cart/checkout routes — the server must NEVER emit the real number as a
     plain JSON key, so we zero / placeholder the amounts those routes return for
     a Salesman (ADR 0001 guardrail).
  2. The portal order DETAIL page + its PDF/report — these render the order
     document full of prices and QWeb-masking every price node is large and
     fragile. A Salesman never needs the priced line view (the Owner prices the
     order), so we BLOCK the whole route for a Salesman and send them back to the
     price-masked order list, which still shows the order's Pending status.

Masking is PRACTICAL, not adversary-proof (ADR 0001): we suppress the rendered
number + the main JSON routes; a determined Salesman with dev tools is out of
scope. Interactive requests key off the CURRENT user's group (the viewer IS the
salesman here); async/owner-context renders are not in this flow (flow A sends
the Salesman no order email — nothing to mask there).
"""

from odoo.http import request, route

from odoo.addons.website_sale.controllers.cart import Cart
from odoo.addons.website_sale.controllers.delivery import Delivery
from odoo.addons.sale.controllers.portal import CustomerPortal

# xmlid of the hidden "no prices" group. Render masking (QWeb `groups=`) keys off
# this too; here we use has_group on the CURRENT user — both are "the viewer IS
# the salesman" checks (ADR 0001).
SALESMAN_GROUP = 'funedistri_customizations.coffin_salesman_group'

# Placeholder HTML returned by the masked JSON routes in place of any amount.
# Mirrors the QWeb "Prix masqué" placeholder (and carries the same CSS class).
_MASKED_AMOUNT_HTML = (
    '<span class="text-muted fst-italic coffin-price-masked">Prix masqué</span>'
)


def _viewer_is_salesman():
    """True when the user making THIS request is a price-blind Salesman.

    Safe for public/no-session requests: has_group on the public user returns
    False, so the shop stays priced for anonymous browsing (the login gate
    handles public access separately).
    """
    return request.env.user.has_group(SALESMAN_GROUP)


class CoffinCart(Cart):
    """Strip real money out of the cart JSON routes for a Salesman.

    QWeb masks prices in the rendered HTML (incl. the HTML fragments these routes
    return), but the routes ALSO return RAW numbers as plain JSON keys that no
    template touches:
      - /shop/cart/update -> ``amount`` (order total) + ``minor_amount``
      - /shop/cart/add    -> ``notification_info.lines[].price_total`` and
                             ``tracking_info[].price`` / ``discount``
    We call super() and zero those keys for a Salesman. Zero (not delete): the
    frontend JS expects the keys; the displayed total is masked anyway, so 0 is
    harmless and never reveals the real figure.
    """

    def update_cart(self, line_id, quantity, product_id=None, **kwargs):
        values = super().update_cart(
            line_id, quantity, product_id=product_id, **kwargs)
        if _viewer_is_salesman():
            values['amount'] = 0.0
            values['minor_amount'] = 0
        return values

    def _get_cart_notification_information(self, order, added_qty_per_line):
        info = super()._get_cart_notification_information(order, added_qty_per_line)
        if _viewer_is_salesman():
            for line in info.get('lines', []):
                line['price_total'] = 0.0
        return info

    def _get_tracking_information(self, order_sudo, line_ids):
        info = super()._get_tracking_information(order_sudo, line_ids)
        if _viewer_is_salesman():
            for item in info:
                item['price'] = 0.0
                item['discount'] = 0.0
        return info


class CoffinDelivery(Delivery):
    """Strip amounts out of the delivery-step JSON routes for a Salesman.

    Two JSON routes feed the checkout's delivery picker money that QWeb masking
    can't reach:
      - /shop/set_delivery_method -> order summary amounts (rendered HTML)
      - /shop/get_delivery_rate   -> carrier ``price`` + rendered ``amount_delivery``
    We replace those with the "Prix masqué" placeholder (and zero the raw price),
    keeping ``success`` truthy so the method stays selectable.
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
            if 'price' in rate:
                rate['price'] = 0.0
            if 'amount_delivery' in rate:
                rate['amount_delivery'] = _MASKED_AMOUNT_HTML
            # Don't imply a zero price via "Free" wording; the placeholder already
            # conveys "hidden".
            rate['is_free_delivery'] = False
        return rate


class CoffinSalePortalMasking(CustomerPortal):
    """Block the order DETAIL page (and its PDF/report) for a Salesman.

    /my/orders/<id> (and ?report_type=pdf/html/text) render the order document
    full of prices. Rather than mask every price node, we deny the whole route
    for a Salesman and send them back to the price-masked order list — they still
    see the order's Pending status there. (v1 simplification: block, not mask. A
    price-masked detail page is a possible later refinement.)
    """

    def portal_order_page(self, order_id, report_type=None, **kw):
        if _viewer_is_salesman():
            return request.redirect('/my/orders')
        return super().portal_order_page(order_id, report_type=report_type, **kw)
