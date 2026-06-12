# -*- coding: utf-8 -*-
# A module's top-level __init__.py runs when Odoo imports the module. It wires up
# the Python sub-packages. models = ORM extensions (sale.order field); controllers
# = our website checkout routes (Step 1: /shop/submit_order). models first so the
# field exists before controllers reference it.
from . import models
from . import controllers
