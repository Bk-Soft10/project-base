from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError

import logging

_logger = logging.getLogger(__name__)


class SaleOrderReturn(models.Model):
    _name = 'sale.order.return'

    name = fields.Char()
    sale_id = fields.Many2one("sale.order", string="Sale Order")
    date = fields.Date(string="Date", default=fields.Date.context_today)
    return_reason = fields.Text("Return Reason")

    picking_id = fields.Many2one("stock.picking", string="Picking")
    return_picking_id = fields.Many2one("stock.picking", string="Return Picking")

    invoice_ids = fields.Many2many(comodel_name="account.move", relation="sale_return_invoice_ids_rel",
                                   string="Invoice")
    refund_invoice_ids = fields.Many2many(comodel_name="account.move", relation="sale_return_refund_invoice_ids_rel",
                                          string="Refund Invoice")

