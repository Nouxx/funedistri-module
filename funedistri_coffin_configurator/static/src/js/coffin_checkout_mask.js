/** @odoo-module **/

// Step 6 fix — keep the checkout "Confirm" button usable for a price-masked
// SALESMAN.
//
// THE BUG this guards against:
//   Our server-side price masking (ADR 0001, price_visibility_templates.xml)
//   REMOVES the whole order-totals table (`div.o_cart_total`, the rows
//   tr[name="o_order_delivery"], o_order_total_untaxed, …) from the checkout page
//   for a Salesman — they must see no amount.
//
//   The native `Checkout` interaction (website_sale/.../interactions/checkout.js)
//   sets up delivery methods on page load (willStart → _prepareDeliveryMethods).
//   That path calls `_disableMainButton()` FIRST, then rates the pre-selected
//   carrier, which ends in `_updateCartSummary()`:
//
//       const amountDelivery = targetEl.querySelector(
//           'tr[name="o_order_delivery"] .monetary_field');
//       ...
//       if (amountDelivery.classList.contains('d-none')) { ... }   // ← throws
//
//   For the Salesman that table is gone, so `amountDelivery` is null and the
//   `.classList` read throws a TypeError. The throw happens BEFORE the code that
//   re-enables the "Confirm" button, so the button keeps the `disabled` class and
//   the Salesman can never leave the address step. (A Store owner keeps the table,
//   so the native code runs fine and the button enables — which is why the bug
//   looked Salesman-specific.)
//
// THE FIX:
//   Patch `_updateCartSummary` to no-op when the totals table is absent. There is
//   genuinely nothing to update for a masked Salesman (the amounts are hidden), so
//   skipping is the correct behaviour AND it removes the throw, letting
//   `_enableMainButton()` run. For everyone else the table exists and we defer to
//   the native implementation unchanged.

import { patch } from "@web/core/utils/patch";
import { Checkout } from "@website_sale/interactions/checkout";

patch(Checkout.prototype, {
    _updateCartSummary(result, targetEl) {
        // No totals table (price-masked Salesman) → nothing to update, and the
        // native code would throw on the missing element. Skip safely.
        if (!targetEl.querySelector('tr[name="o_order_delivery"] .monetary_field')) {
            return;
        }
        return super._updateCartSummary(result, targetEl);
    },
});
