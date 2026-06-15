# -*- coding: utf-8 -*-
# A module's top-level __init__.py runs when Odoo imports the module. It wires up
# the Python sub-packages. models first so fields exist before a route references
# them; controllers second.
from . import models
from . import controllers
