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
    po_price_state = fields.Selection([
        ('price_pending', 'Pending for Pricing'), ('price_ready', 'Ready for Confirmation'),
    ], copy=False, compute='_compute_price_po_status', store=True)
    is_need_po = fields.Boolean(string="Is Need PO", default=False, compute='_compute_is_need_po', store=True)

    def _compute_can_confirm_sale(self):
        for rec in self:
            rec_su = rec.sudo()
            order_lines = rec_su.order_line
            rec_su.can_confirm_so = True if order_lines and all(line._is_valid_price() for line in order_lines) else False

    @api.depends('request_purchase_ids', 'request_purchase_ids.order_line', 'request_purchase_ids.is_confirmed_price', 'order_line.request_purchase_line_ids')
    def _compute_price_po_status(self):
        for rec in self:
            rec_su = rec.sudo()
            rec_su.po_price_state = None
            order_lines = rec_su.order_line.filtered(lambda x: x.is_request_po and x.request_purchase_line_ids)
            if order_lines and len(order_lines) > 0:
                is_valid_price_lines = True if order_lines and all(line.is_price_valid for line in order_lines) else False
                rec_su.po_price_state = 'price_ready' if is_valid_price_lines else 'price_pending'

    @api.depends('request_purchase_ids', 'request_purchase_ids.state', 'order_line', 'order_line.product_id', 'order_line.is_request_po', 'order_line.request_purchase_line_ids')
    def _compute_is_need_po(self):
        for rec in self:
            rec_su = rec.sudo()
            order_lines = rec_su.order_line and rec_su.order_line.filtered(lambda x: x._is_need_request_price()) or None
            rec_su.is_need_po = True if order_lines and len(order_lines) > 0 else False

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
        action_rec = self.env.ref("sale_vendor_prices.action_sale_rfq_wizard_open", None)
        if action_rec and order_lines and len(order_lines) > 0:
            action = action_rec.sudo().read()[0]
            action['context'] = {
                'default_sale_id': sale_rec.id,
                'default_company_id': sale_rec.company_id and sale_rec.company_id.id or self.env.company.id,
                'default_line_ids': [(6, 0, [line.id for line in order_lines])]
            }
            return action
        return {'type': 'ir.actions.act_window_close'}

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
            po_recs = rec_su.request_purchase_ids.filtered(lambda x: x.state in ['draft', 'sent'] and x.is_confirmed_price)
            if po_recs and len(po_recs) > 0:
                for po_rec in po_recs:
                    po_rec.button_confirm()
        return res

    # def action_validate_price(self):
    #     self.ensure_one()
    #     rec_su = self.sudo()
    #     order_lines = rec_su.order_line and rec_su.order_line.filtered(lambda x: x._is_valid_price()) or None
    #     if order_lines and all(line._is_valid_price() for line in order_lines):
    #         rec_su.state = 'draft'
    #     else:
    #         raise UserError(_("No purchase order found for validation."))

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
    is_request_po = fields.Boolean(related='product_id.is_request_po', string="Request PO", store=True)
    is_price_valid = fields.Boolean(string="Price Valid", store=True, compute='_compute_price_valid')

    def _get_request_po_lines(self):
        self.ensure_one()
        rec_su = self.sudo()
        return rec_su.request_purchase_line_ids.filtered(lambda x: x.order_id.state not in ['cancel'])

    def can_create_request_po(self):
        self.ensure_one()
        rec_su = self.sudo()
        return True if rec_su.product_id and not rec_su._is_valid_price() and rec_su._is_need_request_price() else False

    def _is_need_request_price(self):
        self.ensure_one()
        rec_su = self.sudo()
        return True if rec_su.product_id and rec_su.is_request_po and not rec_su._has_request_po() else False

    def _has_request_po(self):
        self.ensure_one()
        rec_su = self.sudo()
        purchase_lines = rec_su._get_request_po_lines()
        return purchase_lines and len(purchase_lines) > 0 or False

    def _is_valid_price(self):
        self.ensure_one()
        rec_su = self.sudo()
        if not rec_su.is_request_po:
            return True
        purchase_lines = rec_su._get_request_po_lines()
        po_lines = purchase_lines and purchase_lines.filtered(lambda x: x.order_id.is_confirmed_price) or None
        return po_lines and len(po_lines) > 0 or False

    @api.depends('product_id.is_request_po', 'request_purchase_line_ids', 'request_purchase_line_ids.price_unit', 'request_purchase_line_ids.order_id.state', 'request_purchase_line_ids.order_id.is_confirmed_price')
    def _compute_price_valid(self):
        for rec in self:
            rec_su = rec.sudo()
            rec_su.is_price_valid = True if rec_su._is_valid_price() else False

    @api.depends('product_id', 'product_uom_id', 'product_uom_qty')
    def _compute_price_unit(self):
        super()._compute_price_unit()
        for rec in self:
            rec_su = rec.sudo()
            po_lines = rec._get_request_po_lines()
            if po_lines:
                rec_su._compute_vendor_price()

    @api.depends('request_purchase_line_ids', 'request_purchase_line_ids.price_unit', 'request_purchase_line_ids.order_id.state')
    def _compute_vendor_price(self):
        for rec in self:
            rec_su = rec.sudo()
            po_lines = rec._get_request_po_lines()
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
    is_confirmed_price = fields.Boolean(string="Is Confirmed Price", default=False)

    def action_confirm_price(self):
        self.ensure_one()
        rec_su = self.sudo()
        rec_su.is_confirmed_price = True

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
        return super().button_confirm()

#################################################################################################################
# purchase.order.line model
#################################################################################################################

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    request_sale_line_id = fields.Many2one('sale.order.line', string='Request Sale Line', copy=False,
                                           domain=[('order_id.state', 'not in', ['cancel'])])

#################################################################################################################
# product.template model
#################################################################################################################

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_request_po = fields.Boolean(string="Request PO", default=False)
