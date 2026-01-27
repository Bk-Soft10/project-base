from . import models
from . import controller
try:
    from odoo.addons import jsonifier
except ImportError:
    from . import jsonifier
