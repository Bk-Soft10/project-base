from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError

import logging

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    is_return_picking = fields.Boolean(compute='_compute_return_picking', store=True)

    @api.depends('move_ids_without_package')
    def _compute_return_picking(self):
        for picking in self:
            picking.is_return_picking = any(m.origin_returned_move_id for m in picking.move_ids_without_package)

