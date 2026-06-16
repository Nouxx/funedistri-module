# -*- coding: utf-8 -*-
# Import each model file. One file per feature (ADR 0006). Step 1 adds the
# submit-order flow's extension of sale.order.
from . import sale_order
from . import website
# Step 2 — roles: b2b_role on the contact + the field->group sync.
from . import res_partner
from . import res_users
from . import address_lock
