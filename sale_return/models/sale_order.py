from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError

import logging

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    main_picking_id = fields.Many2one("stock.picking", compute="compute_main_picking")

    def compute_main_picking(self):
        for rec in self:
            rec.main_picking_id = False
            pickings = rec.picking_ids.filtered(lambda x: x.state != 'cancel' and not x.is_return_picking)
            if pickings:
                rec.main_picking_id = pickings[0]