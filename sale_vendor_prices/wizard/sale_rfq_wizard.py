from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError

#################################################################################################################
#################################################################################################################

class SaleRfqWizard(models.TransientModel):
    _name = 'sale.rfq.wizard'
    _description = 'Sale RFQ Wizard'

    def _get_purchase_responsible_domain(self):
        purchase_grp = self.env.ref('purchase.group_purchase_user')
        group_ids = purchase_grp and purchase_grp.ids[0] or []
        return "[('share', '=', False), ('company_ids', 'in', company_id), ('all_group_ids', 'in', %s)]" % group_ids

    sale_id = fields.Many2one('sale.order', string='Request Sale', required=True, copy=False)
    warehouse_id = fields.Many2one(related='sale_id.warehouse_id', store=True)
    picking_type_id = fields.Many2one('stock.picking.type', string='Picking Type', copy=False, required=True,
                                   domain="[('code', 'in', ['incoming']), ('warehouse_id', '=', warehouse_id)]")
    line_ids = fields.Many2many('sale.order.line', string='Order Lines', copy=False,
                                domain="[('product_id', '!=', False), ('is_request_po', '!=', False), ('order_id', '=', sale_id)]")
    user_id = fields.Many2one('res.users', string='Responsible User', copy=False, domain=_get_purchase_responsible_domain)
    company_id = fields.Many2one('res.company', string='Company', copy=False, required=True,
                                 default=lambda self: self.env.company)

    @api.onchange('sale_id')
    @api.depends('sale_id')
    def _change_sale_record(self):
        for rec in self:
            rec_su = rec.sudo()
            sale_rec = rec_su.sale_id
            wh_st = sale_rec and sale_rec.warehouse_id or None
            if wh_st:
                rec_su.warehouse_id = wh_st.id
            order_lines = sale_rec and sale_rec.order_line.filtered(lambda x: x.can_create_request_po()) or None
            if order_lines and not rec_su.line_ids:
                rec_su.line_ids = [(6, 0, [line.id for line in order_lines])]
            company_rec = sale_rec and sale_rec.company_id or None
            if company_rec:
                rec_su.company_id = company_rec.id

    @api.onchange('warehouse_id')
    @api.depends('warehouse_id')
    def _change_warehouse_record(self):
        for rec in self:
            rec_su = rec.sudo()
            sale_rec = rec_su.sale_id
            wh_st = rec_su.warehouse_id if rec_su.warehouse_id else sale_rec and sale_rec.warehouse_id or None
            picking_type = wh_st and wh_st.in_type_id or None
            if picking_type:
                rec_su.picking_type_id = picking_type.id

    def action_submit(self):
        self.ensure_one()
        rec_su = self.sudo()
        close_act = {'type': 'ir.actions.client', 'tag': 'reload'} or {'type': 'ir.actions.act_window_close'}
        sale_rec = rec_su.sale_id
        picking_type = rec_su.picking_type_id
        sale_lines = rec_su.line_ids.filtered(lambda x: x._is_need_request_price() and x.product_id)
        user_rec = rec_su.user_id or None
        company_rec = rec_su.company_id or self.env.company
        default_vendor = user_rec and user_rec.partner_id or None
        if sale_rec and picking_type and sale_lines and sale_rec.state in ['draft']:
            order_lines = [(0, 0, {
                'name': line.name,
                'product_id': line.product_id and line.product_id.id or None,
                'product_uom_id': line.product_uom_id and line.product_uom_id.id or None,
                'product_qty': line.product_uom_qty,
                'analytic_distribution': line.analytic_distribution,
                'request_sale_line_id': line.id,
            }) for line in sale_lines if line.product_id]
            po_values = {
                'request_sale_id': sale_rec and sale_rec.id or None,
                'picking_type_id': picking_type and picking_type.id or None,
                'company_id': company_rec and company_rec.id or None,
                'user_id': rec_su.user_id and rec_su.user_id.id or None,
                'order_line': order_lines,
                'origin': sale_rec and sale_rec.name or None,
                # 'partner_id': default_vendor and default_vendor.id or self.env.user.partner_id.id,
                # 'date_order': sale_rec and sale_rec.date_order or None,
            }
            po_rec = self.env['purchase.order'].sudo().create(po_values) if order_lines and len(order_lines) > 0 else None
            if po_rec and sale_rec:
                sale_rec.action_price_pending()

            res_message = _("Request Purchase Created Successfully!") if po_rec else _("Request Purchase Creation Failed!")
            res_type = 'success' if po_rec else 'warning'
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': res_message,
                    'type': res_type,
                    'sticky': False,
                    'next': close_act,
                }
            }
        return close_act

    def action_close(self):
        return {'type': 'ir.actions.client', 'tag': 'reload'} or {'type': 'ir.actions.act_window_close'}

