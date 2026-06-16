# -*- coding: utf-8 -*-
"""Locked company address book (ADR 0005, Step 5 + 5b).

A B2B user (Salesman or Store owner) may **never create or edit any address** — at
checkout or in the portal. They may only SELECT among their Customer company's
Owner-defined addresses, with a strict type separation:
  - shipping  ← company *Delivery*-type child contacts only;
  - billing   ← company *Invoice*-type child contacts only;
and the two never cross. Their own contact is neither type, so it is never an order
address. Guards negotiated-shipping margin + billing correctness, so SERVER-enforced
(a UI hide alone is insufficient — a crafted request must be refused):

  checkout (website_sale):
   - shop_address (GET) / shop_address/submit (POST) → refused for ANY address
     (no create/edit at all);
   - shop_update_address → the chosen address must be in the company's allowed set
     OF THE RIGHT TYPE (delivery↔Delivery, billing↔Invoice);
   - _check_cart_and_addresses → auto-assign the first company address of each type
     (so the selection list shows, no loop to the blocked form), and BLOCK checkout
     if the company lacks a Delivery or an Invoice address.
  portal (portal):
   - portal_address (GET) / portal_address/submit (POST) / address_archive → refused.
     (/my/account login-profile editing is left alone; /my/addresses stays viewable.)
"""

from werkzeug.exceptions import Forbidden

from odoo.http import request, route

from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.addons.portal.controllers.portal import CustomerPortal


def _b2b(self_or_none=None):
    """True when the current user is a B2B user (locked out of editing addresses)."""
    return request.env.user._coffin_is_b2b_user()


def _allowed_partner_ids(order_sudo, addr_type):
    """IDs of the company's Owner-defined addresses of the given contact type
    ('delivery' or 'invoice') — the only ones a B2B user may select for that slot."""
    commercial = order_sudo.partner_id.commercial_partner_id
    return set(request.env['res.partner'].sudo()._search([
        ('id', 'child_of', commercial.id),
        ('type', '=', addr_type),
    ]))


class CoffinAddressLock(WebsiteSale):

    def _check_cart_and_addresses(self, order_sudo):
        if order_sudo and _b2b():
            if block := self._coffin_enforce_company_addresses(order_sudo):
                return block
        return super()._check_cart_and_addresses(order_sudo)

    def _coffin_enforce_company_addresses(self, order_sudo):
        """Force the order's billing (and shipping, if deliverable) onto a company
        address of the right type. Returns a redirect (hard stop) when the company
        lacks a required address type, else None."""
        # Billing is always required.
        invoice_ids = _allowed_partner_ids(order_sudo, 'invoice')
        if not invoice_ids:
            return request.redirect('/shop/cart')  # Owner must define an invoice addr
        if order_sudo.partner_invoice_id.id not in invoice_ids:
            order_sudo._update_address(min(invoice_ids), ['partner_invoice_id'])
        # Shipping only for deliverable carts (coffins are goods → deliverable).
        if not order_sudo.only_services:
            delivery_ids = _allowed_partner_ids(order_sudo, 'delivery')
            if not delivery_ids:
                return request.redirect('/shop/cart')  # Owner must define a delivery addr
            if order_sudo.partner_shipping_id.id not in delivery_ids:
                order_sudo._update_address(min(delivery_ids), ['partner_shipping_id'])
        return None

    def shop_address(self, **kw):
        # A B2B user edits no address: block the add/edit form for any type.
        if _b2b():
            return request.redirect('/shop/checkout')
        return super().shop_address(**kw)

    def shop_address_submit(self, **kw):
        # Refuse any create/edit (even a crafted POST that skipped the blocked form).
        if _b2b():
            raise Forbidden("Addresses are managed by Funedistri; "
                            "you may only select an existing one.")
        return super().shop_address_submit(**kw)

    @route('/shop/update_address', type='jsonrpc', auth='public', website=True)
    def shop_update_address(self, partner_id, address_type='billing', **kw):
        if _b2b() and (order_sudo := request.cart):
            wanted = 'invoice' if address_type == 'billing' else 'delivery'
            if int(partner_id) not in _allowed_partner_ids(order_sudo, wanted):
                raise Forbidden(
                    "This address is not an allowed %s address for your company."
                    % address_type)
        return super().shop_update_address(partner_id, address_type=address_type, **kw)


class CoffinPortalAddressLock(CustomerPortal):
    """Block address create/edit in the portal too (the checkout lock would be
    pointless if a B2B user could edit the same addresses under /my)."""

    def portal_address(self, **kw):
        if _b2b():
            return request.redirect('/my/addresses')  # view-only, no add/edit form
        return super().portal_address(**kw)

    def portal_address_submit(self, **kw):
        if _b2b():
            raise Forbidden("Addresses are managed by Funedistri.")
        return super().portal_address_submit(**kw)

    def address_archive(self, partner_id):
        if _b2b():
            raise Forbidden("Addresses are managed by Funedistri.")
        return super().address_archive(partner_id)
