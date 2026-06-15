# -*- coding: utf-8 -*-
"""Submit-order flow — extensions to Odoo's ``sale.order`` (Step 1, tracer spine).

Flow A (CLAUDE.md): checkout has NO online payment. A B2B user fills a cart and
hits "Valider la commande"; that hands the cart to the Owner as a **Pending**
Order. The Owner later Validates it (``action_confirm()``: draft -> sale).

Key Odoo fact: the cart a user fills IS already a ``sale.order`` in ``draft``.
So submitting creates nothing — it FLAGS the existing draft as submitted and
notifies the Owner. "Pending" = draft + submitted.
"""

from odoo import fields, models


class SaleOrder(models.Model):
    # _inherit (not _name): we EXTEND the core sale.order, adding a field + helpers
    # rather than defining a new model. Standard Odoo way to bolt onto a core model.
    _inherit = 'sale.order'

    # WHY this field exists:
    # A shopping cart and a freshly-submitted Order are BOTH 'draft' sale.orders —
    # Odoo has no native flag to tell them apart. Flow A keeps a submitted Order in
    # 'draft' (= "Pending", awaiting Validate), so without a marker we could not
    # list submitted Orders in the portal without also listing abandoned carts.
    # The submit controller flips this True; the portal domain then shows
    # "draft AND submitted" (Pending) and still hides live carts.
    coffin_is_submitted = fields.Boolean(
        string="Submitted (Pending validation)",
        default=False,
        copy=False,  # a duplicated order should start as a fresh, un-submitted cart
        help="Set when a B2B user submits this Order at checkout. Distinguishes a "
             "Pending Order (draft + submitted) from a live shopping cart "
             "(draft + not submitted).",
    )

    def _coffin_submit_as_pending(self):
        """Turn this draft cart into a Pending Order and notify the Owner.

        Called by the /shop/submit_order controller. Kept on the model (not in the
        controller) so the behaviour is unit-testable without the web layer.
        """
        self.ensure_one()
        # Flag it Pending. We deliberately do NOT confirm — it stays 'draft' until
        # the Owner Validates, so the price-blind Salesman never triggers a confirm
        # email or locks the Owner out of editing.
        self.coffin_is_submitted = True
        self._coffin_notify_owner()

    def _coffin_notify_owner(self):
        """Tell the Owner a new Order is waiting — activity (primary) + email nudge.

        - Activity = a durable native "To Do" on the Order, assigned to the Owner;
          it stays in their list until acted on. This is the "no Order sits unseen"
          guarantee (CLAUDE.md).
        - Email = a nudge to come look, since the Owner isn't always in the backend.

        Step 1 has no roles yet, so "the Owner" = the order's salesperson
        (``user_id``), falling back to the admin user. Step 2 (roles) will refine
        who the Owner is.
        """
        self.ensure_one()
        owner = self.user_id or self.env.ref('base.user_admin',
                                             raise_if_not_found=False)
        if owner:
            # activity_schedule comes from mail.thread (sale.order inherits it).
            # 'mail.mail_activity_data_todo' is Odoo's generic "To Do" activity type.
            self.activity_schedule(
                'mail.mail_activity_data_todo',
                summary="À valider — nouvelle commande",
                note="Une nouvelle commande a été soumise et attend votre "
                     "validation.",
                user_id=owner.id,
            )
        # Email nudge. Template lives in data/mail_template_owner_order.xml; it
        # emails the salesperson. raise_if_not_found=False so a missing template
        # never blocks a submit (the activity is the real guarantee).
        template = self.env.ref(
            'funedistri_customizations.mail_template_owner_order_submitted',
            raise_if_not_found=False,
        )
        if template:
            # force_send=False → queue the mail (Odoo's cron sends it); avoids a
            # slow SMTP call inside the user's submit request.
            template.send_mail(self.id, force_send=False)
