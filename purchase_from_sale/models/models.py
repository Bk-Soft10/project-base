from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)

#################################################################################################################
# sale.order model
#################################################################################################################

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    request_purchase_ids = fields.One2many('purchase.order', 'request_sale_id', string='Purchases', copy=False)
    request_purchase_count = fields.Integer("Count of Source PO", compute='_compute_request_purchase_count')

    @api.depends('request_purchase_ids', 'request_purchase_ids.state')
    def _compute_request_purchase_count(self):
        for rec in self:
            rec_su = rec.sudo()
            po_recs = rec_su.request_purchase_ids and rec_su.request_purchase_ids.filtered(lambda p: p.state not in ['cancel']) or None
            rec.request_purchase_count = len(po_recs.ids) if po_recs else 0

    def action_view_request_purchases(self):
        self.ensure_one()
        po_recs = self.request_purchase_ids.filtered(lambda p: p.state not in ['cancel'])
        if not po_recs:
            return {'type': 'ir.actions.act_window_close'}
        action_rec = self.env.ref("purchase.purchase_rfq", None)
        action = action_rec.sudo().read()[0] if action_rec else {}
        action['domain'] = [('id', 'in', po_recs.ids or [])]
        action['context'] = {'default_request_sale_id': self.ids[0], 'request_sale_id': self.ids[0]}
        view_ref = self.env.ref('purchase.purchase_order_form', None)
        if po_recs and len(po_recs.ids) == 1 and view_ref:
            form_view = [(view_ref.id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state, view) for state, view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = po_recs.ids[0]
        return action

#################################################################################################################
# sale.order.line model
#################################################################################################################

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    request_purchase_line_ids = fields.One2many('purchase.order.line', 'request_sale_line_id',
                                                string='Request Purchase Lines', copy=False)

#################################################################################################################
# purchase.order model
#################################################################################################################

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    request_sale_id = fields.Many2one('sale.order', string='Request Sale', copy=False)

#################################################################################################################
# purchase.order.line model
#################################################################################################################

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    request_sale_line_id = fields.Many2one('sale.order.line', string='Request Sale Line', copy=False)
