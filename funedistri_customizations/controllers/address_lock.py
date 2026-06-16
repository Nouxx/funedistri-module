# -*- coding: utf-8 -*-
"""Locked company address book (Step 5, ADR 0005).

A B2B user may only SELECT among their Customer company's Owner-defined DELIVERY
addresses at checkout — never create or edit one (negotiated shipping rates apply
only to vetted addresses; a new address could break margin). Scope = the delivery
address only; the billing/invoice address keeps native behaviour.

This guards real money, so it is SERVER-enforced (ADR 0005), not just a UI hide
(the "Add Address" button is also hidden — views/address_lock_templates.xml — but
that is UX; a crafted request must still be refused here):

  - shop_address (GET form)     → blocked for a B2B user on delivery (and on a
                                  "use delivery as billing" create, which would
                                  set a new delivery too). Redirects to checkout.
  - shop_address/submit (POST)  → same, refused (Forbidden) so a crafted create/
                                  edit cannot slip a new delivery address in.
  - shop_update_address (select)→ the chosen delivery address must be one of the
                                  company's Owner-defined delivery addresses; a
                                  rogue id is refused (Forbidden).

"Company address" = a native child contact of the company `res.partner` with
``type='delivery'`` (the Owner creates them in the backend). No custom model.
"""

from werkzeug.exceptions import Forbidden

from odoo.http import request, route
from odoo.tools import str2bool

from odoo.addons.website_sale.controllers.main import WebsiteSale


def _delivery_locked():
    """True when the current user is a B2B user whose delivery address is locked."""
    return request.env.user._coffin_is_b2b_user()


def _allowed_delivery_partner_ids(order_sudo):
    """IDs of the company's Owner-defined delivery addresses (the only selectable
    delivery addresses for a B2B user)."""
    commercial = order_sudo.partner_id.commercial_partner_id
    return set(request.env['res.partner'].sudo()._search([
        ('id', 'child_of', commercial.id),
        ('type', '=', 'delivery'),
    ]))


class CoffinAddressLock(WebsiteSale):

    def _check_cart_and_addresses(self, order_sudo):
        # A B2B user cannot create a delivery address, so the order must already
        # carry one of the company's. If it doesn't (e.g. it still defaults to the
        # user's own contact), assign the first company delivery address — else
        # native would redirect to the (blocked) create form and loop. The user
        # can then switch among the company's addresses via the checkout list.
        if _delivery_locked() and order_sudo:
            allowed = _allowed_delivery_partner_ids(order_sudo)
            if allowed and order_sudo.partner_shipping_id.id not in allowed:
                order_sudo._update_address(min(allowed), ['partner_shipping_id'])
        return super()._check_cart_and_addresses(order_sudo)

    def shop_address(
        self, partner_id=None, address_type='billing', use_delivery_as_billing=None,
        **query_params
    ):
        # A B2B user cannot open the add/edit form for a delivery address (nor a
        # "use delivery as billing" create, which would set a new delivery too).
        if _delivery_locked() and (
            address_type == 'delivery'
            or str2bool(use_delivery_as_billing or 'false')
        ):
            return request.redirect('/shop/checkout')
        return super().shop_address(
            partner_id=partner_id, address_type=address_type,
            use_delivery_as_billing=use_delivery_as_billing, **query_params)

    def shop_address_submit(
        self, partner_id=None, address_type='billing', use_delivery_as_billing=None,
        callback=None, **form_data
    ):
        # Refuse any create/edit that would touch the delivery address for a B2B
        # user — even via a crafted POST that skipped the (hidden/blocked) form.
        if _delivery_locked() and (
            address_type == 'delivery'
            or str2bool(use_delivery_as_billing or 'false')
        ):
            raise Forbidden(
                "Delivery addresses are managed by Funedistri; "
                "you may only select an existing one.")
        return super().shop_address_submit(
            partner_id=partner_id, address_type=address_type,
            use_delivery_as_billing=use_delivery_as_billing, callback=callback,
            **form_data)

    @route('/shop/update_address', type='jsonrpc', auth='public', website=True)
    def shop_update_address(self, partner_id, address_type='billing', **kw):
        # For a B2B user, the chosen DELIVERY address must be one the Owner defined
        # for the company. (Native only checks "is a child contact" and allows any
        # type — too loose for the negotiated-shipping rule.)
        if (
            address_type == 'delivery'
            and _delivery_locked()
            and (order_sudo := request.cart)
            and int(partner_id) not in _allowed_delivery_partner_ids(order_sudo)
        ):
            raise Forbidden("This delivery address is not allowed for your company.")
        return super().shop_update_address(
            partner_id, address_type=address_type, **kw)
