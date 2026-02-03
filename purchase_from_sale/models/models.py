from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)

#################################################################################################################
# sale.order model
#################################################################################################################

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    request_purchase_ids = fields.One2many('purchase.order', 'request_sale_id', string='Purchases', copy=False,
                                           domain=[('state', 'not in', ['cancel'])])
    request_purchase_count = fields.Integer("Count of RFQs", compute='_compute_request_purchase_count')
    can_confirm_so = fields.Integer("Can Confirm Order", compute='_compute_can_confirm_sale')
    state = fields.Selection(selection_add=[
        ('draft',), ('price_pending', 'Pending for Pricing'), ('ready', 'Ready for Confirmation'), ('sent',),
    ], ondelete={'price_pending': 'set default', 'ready': 'set default'})

    def _compute_can_confirm_sale(self):
        for rec in self:
            rec_su = rec.sudo()
            po_recs = rec_su.request_purchase_ids and rec_su.request_purchase_ids.filtered(lambda p: p.state not in ['cancel']) or None
            rec.can_confirm_so = True if not po_recs or po_recs.filtered(lambda p: p.state in ['vendor_price_confirmed']) else False

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

    def action_cancel(self):
        res = super().action_cancel()
        for rec in self:
            rec_su = rec.sudo()
            po_recs = rec_su.request_purchase_ids.filtered(lambda x: x.state not in ['cancel'])
            if any(order.locked or order.state in ['purchase', 'done'] for order in po_recs):
                raise UserError(_("You cannot cancel a locked or confirmed order. Please unlock or confirm it first."))
            for po_rec in po_recs:
                po_rec.button_cancel()
        return res

    def action_confirm(self):
        res = super().action_confirm()
        for rec in self:
            rec_su = rec.sudo()
            po_recs = rec_su.request_purchase_ids.filtered(lambda x: x.state in ['vendor_price_confirmed'])
            if po_recs and len(po_recs) == 1:
                po_recs.button_confirm()
        return res

    def action_validate_price(self):
        self.ensure_one()
        rec_su = self.sudo()
        po_recs = rec_su.request_purchase_ids.filtered(lambda x: x.state in ['vendor_price_confirmed'])
        po_order_lines = rec_su.order_line.filtered(lambda x: x.request_purchase_line_ids)
        valid_prices = all(line.request_purchase_line_ids.filtered(lambda x: x.order_id.state in ['vendor_price_confirmed']) for line in po_order_lines)
        if po_recs and len(po_recs) == 1 and valid_prices:
            rec_su.action_ready()
        else:
            raise UserError(_("No purchase order found for validation."))

    def message_post(self, **kwargs):
        if self.env.context.get('mark_so_as_sent'):
            self.filtered(lambda o: o.state in ['draft', 'ready']).with_context(tracking_disable=True).write({'state': 'sent'})
            kwargs['notify_author_mention'] = kwargs.get('notify_author_mention', True)
        return super().message_post(**kwargs)

#################################################################################################################
# sale.order.line model
#################################################################################################################

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    request_purchase_line_ids = fields.One2many('purchase.order.line', 'request_sale_line_id', string='Purchase Lines',
                                                copy=False, domain=[('order_id.state', 'not in', ['cancel'])])
    price_vendor = fields.Float(string="Vendor Price", compute='_compute_vendor_price', digits='Product Price',
                                store=True, readonly=True)
    price_sale = fields.Float(string="Sale Price", compute='_compute_price_sale_unit', digits='Product Price',
                              store=True, readonly=True)

    def can_create_request_po(self):
        self.ensure_one()
        rec_su = self.sudo()
        return True if rec_su.product_id and not rec_su._has_request_po() else False

    def _has_request_po(self):
        self.ensure_one()
        rec_su = self.sudo()
        purchase_lines = rec_su.request_purchase_line_ids.filtered(lambda x: x.order_id.state not in ['cancel'])
        return purchase_lines and len(purchase_lines) > 0 or False

    @api.depends('product_id', 'product_uom_id', 'product_uom_qty')
    def _compute_price_unit(self):
        super()._compute_price_unit()
        for rec in self:
            rec_su = rec.sudo()
            po_lines = rec.request_purchase_line_ids.filtered(lambda x: x.order_id.state not in ['cancel'])
            if po_lines:
                rec_su._compute_vendor_price()

    @api.depends('request_purchase_line_ids', 'request_purchase_line_ids.price_unit', 'request_purchase_line_ids.order_id.state')
    def _compute_vendor_price(self):
        for rec in self:
            rec_su = rec.sudo()
            po_lines = rec_su.request_purchase_line_ids.filtered(lambda x: x.order_id.state not in ['cancel'])
            rec_su.price_vendor = po_lines and po_lines[0].price_unit or 0.0
            if po_lines and po_lines[0].currency_id != rec_su.currency_id:
                vendor_price = po_lines[0].currency_id._convert(
                    po_lines[0].price_unit,
                    rec_su.currency_id,
                    rec_su.company_id,
                    fields.Date.today()
                )
                rec_su.price_vendor = vendor_price
            if rec_su.price_vendor > 0.0:
                rec_su._compute_price_sale_unit()

    @api.depends('product_id', 'product_uom_id', 'product_uom_qty', 'price_vendor', 'price_unit')
    def _compute_price_sale_unit(self):
        for rec in self:
            rec_su = rec.sudo()
            sale_rec = rec_su.order_id or None
            company_rec = sale_rec and sale_rec.company_id or rec_su.company_id or self.env.company
            price_type = company_rec and company_rec.sale_price_type or 'percentage'
            sale_margin = company_rec and company_rec.sale_profit_margin or 5.0
            vendor_price = rec_su.price_vendor or 0.0
            profit_margin = rec_su.price_unit or 0.0
            if vendor_price > 0.0:
                if price_type == 'percentage':
                    sale_margin = vendor_price * sale_margin / 100.0
                profit_margin = sale_margin + vendor_price
            rec_su.price_sale = profit_margin
            rec.price_unit = profit_margin

#################################################################################################################
# purchase.order model
#################################################################################################################

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    partner_id = fields.Many2one(required=False)
    request_sale_id = fields.Many2one('sale.order', string='Request Sale', copy=False, domain=[('state', 'not in', ['cancel'])])
    state = fields.Selection(selection_add=[
        ('sent',), ('vendor_price_confirmed', 'Vendor Price Confirmed'), ('to approve',),
    ], ondelete={'vendor_price_confirmed': 'set default'})

    def action_confirm_price(self):
        self.ensure_one()
        rec_su = self.sudo()
        rec_su.state = 'vendor_price_confirmed'
        sale_rec = rec_su.request_sale_id
        if sale_rec and sale_rec.state in ['price_pending']:
            sale_rec.action_validate_price()

    def button_approve(self, force=False):
        for rec in self:
            rec_su = rec.sudo()
            sale_rec = rec_su.request_sale_id
            if sale_rec and sale_rec.state not in ['sale']:
                raise UserError(_("You cannot approve purchase order before sale order is confirmed."))
        return super().button_approve(force=force)

    def button_confirm(self):
        for rec in self:
            rec_su = rec.sudo()
            sale_rec = rec_su.request_sale_id
            if sale_rec and sale_rec.state not in ['sale']:
                raise UserError(_("You cannot confirm purchase order before sale order is confirmed."))
            if sale_rec and rec_su.state in ['vendor_price_confirmed']:
                rec_su.state = 'draft'
        return super().button_confirm()

#################################################################################################################
# purchase.order.line model
#################################################################################################################

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    request_sale_line_id = fields.Many2one('sale.order.line', string='Request Sale Line', copy=False,
                                           domain=[('order_id.state', 'not in', ['cancel'])])
