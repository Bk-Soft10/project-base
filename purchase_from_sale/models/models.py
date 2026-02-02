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
    request_purchase_count = fields.Integer("Count of RFQs", compute='_compute_request_purchase_count')
    can_confirm_so = fields.Integer("Can Confirm Order", compute='_compute_can_confirm_sale')
    state = fields.Selection(selection_add=[
        ('draft',), ('price_pending', 'Pending for Pricing'), ('ready', 'Ready for Confirmation'), ('sent',),
    ], ondelete={'price_pending': 'set default', 'ready': 'set default'})

    def _compute_can_confirm_sale(self):
        for rec in self:
            rec_su = rec.sudo()
            po_recs = rec_su.request_purchase_ids and rec_su.request_purchase_ids.filtered(lambda p: p.state not in ['cancel']) or None
            rec.can_confirm_so = len(po_recs.ids) == 0 if po_recs else True

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

    def action_create_rfq_purchase(self):
        self.ensure_one()
        sale_rec = self.sudo()
        order_lines = sale_rec and sale_rec.order_line.filtered(lambda x: x.can_create_request_po()) or None
        action_rec = self.env.ref("purchase_from_sale.action_sale_rfq_wizard_open", None)
        if action_rec and order_lines and len(order_lines) > 0:
            action = action_rec.sudo().read()[0]
            action['context'] = {
                'default_sale_id': sale_rec.id,
                'default_company_id': sale_rec.company_id and sale_rec.company_id.id or self.env.company.id,
                'default_line_ids': [(6, 0, [line.id for line in order_lines])]
            }
            return action
        return {'type': 'ir.actions.act_window_close'}

    def action_price_pending(self):
        self.ensure_one()
        rec_su = self.sudo()
        rec_su.state = 'price_pending'

    def action_ready(self):
        self.ensure_one()
        rec_su = self.sudo()
        rec_su.state = 'ready'

#################################################################################################################
# sale.order.line model
#################################################################################################################

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    request_purchase_line_ids = fields.One2many('purchase.order.line', 'request_sale_line_id', string='Purchase Lines', copy=False)

    def can_create_request_po(self):
        self.ensure_one()
        rec_su = self.sudo()
        return True if rec_su.product_id and not rec_su._has_request_po() else False

    def _has_request_po(self):
        self.ensure_one()
        rec_su = self.sudo()
        purchase_lines = rec_su.request_purchase_line_ids.filtered(lambda x: x.order_id.state not in ['cancel'])
        return purchase_lines and len(purchase_lines) > 0 or False

#################################################################################################################
# purchase.order model
#################################################################################################################

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    partner_id = fields.Many2one(required=False)
    request_sale_id = fields.Many2one('sale.order', string='Request Sale', copy=False)
    state = fields.Selection(selection_add=[
        ('sent',), ('vendor_price_confirmed', 'Vendor Price Confirmed'), ('to approve',),
    ], ondelete={'vendor_price_confirmed': 'set default'})

    def action_confirm_price(self):
        self.ensure_one()
        rec_su = self.sudo()
        rec_su.state = 'vendor_price_confirmed'

#################################################################################################################
# purchase.order.line model
#################################################################################################################

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    request_sale_line_id = fields.Many2one('sale.order.line', string='Request Sale Line', copy=False)
