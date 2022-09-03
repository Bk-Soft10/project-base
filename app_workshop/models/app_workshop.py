# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta, date
from dateutil import relativedelta
import time


# from dateutil import relativedelta

#########################################################################
######  Workshop Appointments data  ##########
#########################################################################

class app_workshop_appointments(models.Model):
    _name = 'app.workshop.appointments'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _description = 'Workshop Appointments Information'
    _order = 'create_date desc'

    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle', required=True, copy=False)
    partner_id = fields.Many2one('res.partner', string='Customer', readonly=True, store=True,
                                 related='vehicle_id.driver_id', copy=False)
    license_plate = fields.Char(string='License plate', copy=False, store=True, readonly=True,
                                related='vehicle_id.license_plate')
    vin_sn = fields.Char(string='Chassis Number', copy=False, store=True, readonly=True, related='vehicle_id.vin_sn')
    brand_id = fields.Many2one('fleet.vehicle.model.brand', string='Brand', related="vehicle_id.model_id.brand_id",
                               store=True, readonly=True)
    model_id = fields.Many2one('fleet.vehicle.model', string='Model', related="vehicle_id.model_id", store=True,
                               readonly=True)
    by_name = fields.Char(string='Driver Name', copy=False)
    phone = fields.Char(string='Phone', copy=False)
    date = fields.Datetime(string="Date", copy=False, default=fields.Datetime.now())
    c_note = fields.Text('Customer Requests Note')
    service_type = fields.Selection(selection=[('a', 'A'), ('b', 'B'), ('c', 'C'), ('d', 'D')], string='Service Type',
                                    copy=False, default='a')
    state = fields.Selection(
        [('draft', 'Draft'), ('confirm', 'Confirmed'), ('order', 'Work-Order'), ('cancel', 'Cancel')], string='State',
        copy=False, default='draft')
    workshop_id = fields.Many2one('app.workshop', string='Work-Order', required=False, copy=False, readonly=True)

    def set_draft(self):
        for rec in self:
            rec.state = 'draft'

    def set_confirm(self):
        for rec in self:
            rec.state = 'confirm'

    def set_order(self):
        for rec in self:
            type_id = self.env.ref('app_workshop.type_work_order')
            order = self.env['app.workshop'].create(
                {'partner_id': rec.partner_id.id, 'vehicle_id': rec.vehicle_id.id, 'by_name': rec.by_name,
                 'phone': rec.phone, 'c_note': rec.c_note, 'type_id': type_id.id})
            if order:
                order.get_data_vehicle_id()
                rec.workshop_id = order.id
                rec.state = 'order'

    def set_cancel(self):
        for rec in self:
            rec.state = 'cancel'


#########################################################################
######  Workshop data  ##########
#########################################################################

class app_workshop(models.Model):
    _name = 'app.workshop'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _description = 'Workshop Data Information'
    _order = 'create_date desc'
    _rec_name = 'no'

    no = fields.Char(string='Workshop-Order-NO', required=True, copy=False, default='/', store=True)
    parent_id = fields.Many2one('app.workshop', string='Parent Work-Order', required=False, copy=False, readonly=True)
    stage_id = fields.Many2one('app.workshop.stage', string='Stage', copy=False)
    type_id = fields.Many2one('app.workshop.type', string='Type', required=False, copy=False)
    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle', required=True, copy=False)
    service_advisor = fields.Many2one('res.users', string='Service Advisor', copy=False,
                                      default=lambda self: self.env.user)
    partner_id = fields.Many2one('res.partner', string='Customer', copy=False)
    license_plate = fields.Char(string='License plate', copy=False, store=True, readonly=True,
                                related='vehicle_id.license_plate')
    vin_sn = fields.Char(string='Chassis Number', copy=False, store=True, readonly=True, related='vehicle_id.vin_sn')
    brand_id = fields.Many2one('fleet.vehicle.model.brand', string='Brand', related='vehicle_id.model_id.brand_id',
                               store=True, readonly=True)
    model_id = fields.Many2one('fleet.vehicle.model', string='Model', related='vehicle_id.model_id', store=True,
                               readonly=True)
    odometer = fields.Float(string='Last Odometer')
    by_name = fields.Char(string='Driver Name', copy=False)
    phone = fields.Char(string='Phone', copy=False)
    line_ids = fields.One2many('app.workshop.line', 'workshop_id', string='Service Task', copy=False)
    order_spare_ids = fields.One2many('app.workshop.spare.order', 'workshop_id', string='Order Spare List', copy=False)
    spare_ids = fields.One2many('app.workshop.spare', 'workshop_id', string='Spare Parts', copy=False)
    picking_ids = fields.One2many('stock.picking', 'workshop_id', string='Picking List', copy=False)
    backorder_ids = fields.One2many('app.workshop', 'parent_id', string='Workshop Back-Orders', copy=False)
    invoice_ids = fields.One2many('account.move', 'workshop_id', string='Invoices', copy=False)
    payment_ids = fields.One2many('account.payment', 'workshop_id', string='Payments', copy=False)
    date_dua = fields.Date(string='Date Due', copy=False, default=fields.Date.today())
    date_in = fields.Datetime(string='Working Date', copy=False, default=fields.Datetime.now())
    date_out = fields.Datetime(string='Delivery Date', copy=False, default=fields.Datetime.now())
    note = fields.Text('Note')
    c_note = fields.Text('Customer Requests Note')
    t_note = fields.Text('Technical Advisor Notes')
    barcode = fields.Char('Barcode', readonly=True, store=True)
    cust_inv = fields.Float(string='Expected Receivable', readonly=True, copy=False, store=True)
    cust_pay = fields.Float(string='Actual Receivable', readonly=True, copy=False, store=True)
    cust_mergin = fields.Float(string='Receivable Dua', readonly=True, copy=False, store=True,
                               compute='get_mergin_account')
    payment_type = fields.Selection(
        selection=[('cash', 'Cash'), ('credit', 'Credit'), ('insurance', 'Insurance'), ('redo job', 'Redo Job'),
                   ('promotion', 'Promotion'), ('warranty', 'Warranty'), ('company cars', 'Company Cars')],
        string='Payment Type', copy=False, default='cash')
    state = fields.Selection([('draft', 'Draft'), ('in_work', 'In Working'), ('done', 'Done'), ('follow', 'Follow Up'),
                              ('cancel', 'Cancel')], string='State', copy=False, default='draft')

    @api.model
    def default_get(self, fields):
        res = super(app_workshop, self).default_get(fields)
        type_id = self.env.ref('app_workshop.type_work_order', False)
        if type_id:
            res.update({'type_id': type_id.id or False})
        return res

    @api.model
    def create(self, vals):
        # bar = self.env['ir.sequence'].get('workshop.barcode.no.sequence')
        # vals['barcode'] = bar
        code = "WO" + self.env['ir.sequence'].get('workshop.no.sequence')
        vals['no'] = code
        res = super(app_workshop, self).create(vals)
        if res.state == 'draft':
            res.get_workshop_no()
            res.get_workshop_barcode()
        return res

    @api.onchange('vehicle_id')
    def get_data_vehicle_id(self):
        for rec in self:
            if rec.vehicle_id:
                rec.partner_id = rec.vehicle_id.driver_id.id if rec.vehicle_id.driver_id else False
                rec.model_id = rec.vehicle_id.model_id.id
                rec.brand_id = rec.vehicle_id.brand_id.id
                rec.license_plate = rec.vehicle_id.license_plate
                rec.vin_sn = rec.vehicle_id.vin_sn
                rec.odometer = rec.vehicle_id.odometer

    def update_odometer_fleet(self):
        for rec in self:
            if rec.vehicle_id and rec.odometer < rec.vehicle_id.odometer:
                rec.vehicle_id.write({'odometer': rec.odometer})

    def set_wk_draft(self):
        for rec in self:
            rec.state = 'draft'

    def set_wk_in_work(self):
        for rec in self:
            rec.state = 'in_work'
            rec.date_in = datetime.now()

    def set_wk_done(self):
        for rec in self:
            rec.state = 'done'
            rec.date_out = datetime.now()
            rec.inv_payment_create()

    def set_wk_cancel(self):
        for rec in self:
            rec.state = 'cancel'

    def inv_payment_create(self):
        for work_order in self:
            line_lst = []
            for line in work_order.line_ids:
                if line.state == 'done':
                    line_lst.append((0, 0,
                                     {'product_id': line.product_id.id, 'quantity': line.qty, 'price_unit': line.price,
                                      'name': line.product_id.name, 'uom_id': line.product_id.uom_id.id,
                                      'account_id': line.product_id.property_account_expense_id.id}))
            for line in work_order.spare_ids:
                if line.state == 'done':
                    line_lst.append((0, 0,
                                     {'product_id': line.product_id.id, 'quantity': line.qty, 'price_unit': line.price,
                                      'name': line.product_id.name, 'uom_id': line.product_id.uom_id.id,
                                      'account_id': line.product_id.property_account_expense_id.id}))
            inv = self.env['account.move'].create({
                'workshop_id': work_order.id,
                'partner_id': work_order.partner_id.id,
                'type': 'out_invoice',
                'journal_type': 'sale',
                'invoice_line_ids': line_lst,
            })
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'account.move',
                'view_mode': 'form',
                'res_id': inv.id
            }

    @api.depends('invoice_ids', 'payment_ids')
    def get_mergin_account(self):
        for rec in self:
            if rec.invoice_ids:
                rec.cust_inv = sum(inv.amount_total for inv in rec.invoice_ids if
                                   inv.type == 'out_invoice' and inv.workshop_id.id == rec.id)
            if rec.payment_ids:
                rec.cust_pay = sum(pay.amount for pay in rec.payment_ids if
                                   pay.payment_type == 'inbound' and pay.workshop_id.id == rec.id)
            if rec.cust_inv:
                rec.cust_mergin = rec.cust_pay - rec.cust_inv

    @api.onchange('invoice_ids')
    def get_data_inv(self):
        for rec in self:
            if rec.invoice_ids:
                rec.cust_inv = sum(inv.amount_total for inv in rec.invoice_ids if
                                   inv.type == 'out_invoice' and inv.workshop_id.id == rec.id)

    @api.onchange('payment_ids')
    def get_data_pay(self):
        for rec in self:
            if rec.payment_ids:
                rec.cust_pay = sum(pay.amount for pay in rec.payment_ids if
                                   pay.payment_type == 'inbound' and pay.workshop_id.id == rec.id)


#########################################################################
######  workshop Stage  ##########
#########################################################################

class app_workshop_stage(models.Model):
    _name = 'app.workshop.stage'
    _description = 'Workshop Stage Information'
    name = fields.Char(string='Name', required=True, copy=False)
    active = fields.Boolean('Active', default=True)


#########################################################################
######  workshop line  ##########
#########################################################################

class app_workshop_line(models.Model):
    _name = 'app.workshop.line'
    _description = 'Workshop Service Information'
    workshop_id = fields.Many2one('app.workshop', string='Work-Order')
    name = fields.Char(string='Description', copy=False, required=True)
    product_id = fields.Many2one('product.product', string='Service', domain=[('type', '=', 'service')], copy=False)
    product_tmpl_id = fields.Many2one('product.template', string='Item Service', domain=[('type', '=', 'service')],
                                      readonly=True, store=True, related='product_id.product_tmpl_id')
    employee_id = fields.Many2one('hr.employee', string='Mechanic', copy=False)
    qty = fields.Float('Quantity', copy=False, default=1.00)
    price = fields.Float('Price', copy=False)
    date_start = fields.Datetime(string='Last Start Date', readonly=True)
    date_end = fields.Datetime(string='Last Finish Date', readonly=True)
    service_time = fields.Float(string='Service Time', readonly=True)
    stander_time = fields.Float(string='Stander Time', readonly=True, store=True,
                                related='product_tmpl_id.stander_time')
    wk_state = fields.Selection(related='workshop_id.state')
    state = fields.Selection(
        [('draft', 'Draft'), ('start', 'Started'), ('puase', 'Puased'), ('done', 'Done'), ('cancel', 'Cancel')],
        string='State', copy=False, default='draft')

    @api.onchange('product_id')
    def change_pro_id(self):
        for rec in self:
            if rec.product_id:
                rec.name = rec.product_id.name
                rec.price = rec.product_id.lst_price

    def set_start(self):
        for rec in self:
            rec.state = 'start'
            rec.date_start = datetime.now()

    def set_puase(self):
        for rec in self:
            rec.state = 'puase'
            if rec.date_start:
                time_pass_date = relativedelta.relativedelta(datetime.now(), rec.date_start)
                time_pass = float(time_pass_date.minutes)
                if time_pass > 0:
                    rec.service_time = rec.service_time + time_pass

    def set_draft(self):
        for rec in self:
            rec.state = 'draft'

    def set_done(self):
        for rec in self:
            rec.state = 'done'
            rec.date_end = datetime.now()
            if rec.date_start:
                time_pass_date = relativedelta.relativedelta(datetime.now(), rec.date_start)
                time_pass = float(time_pass_date.minutes)
                if time_pass > 0:
                    rec.service_time = rec.service_time + time_pass

    def set_cancel(self):
        for rec in self:
            rec.state = 'cancel'


#########################################################################
######  workshop order spare  ##########
#########################################################################

class app_workshop_spare_order(models.Model):
    _name = 'app.workshop.spare.order'
    _description = 'Workshop Spare Order Information'
    _rec_name = 'no'
    no = fields.Char(string='Order-Spare-NO', copy=False, default=lambda self: _('New'), store=True)
    workshop_id = fields.Many2one('app.workshop', string='Work-Order')
    line_id = fields.Many2one('app.workshop.line', string='Service Task')
    pick_id = fields.Many2one('stock.picking', string='Picking', copy=False, readonly=True)
    type_id = fields.Many2one('app.workshop.type', string='Type', store=True, readonly=True,
                              related='workshop_id.type_id', copy=False)
    date = fields.Date(string='Date', copy=False, default=fields.Date.today())
    spare_ids = fields.One2many('app.workshop.spare', 'spare_order_id', string='Spare List')
    wk_state = fields.Selection(related='workshop_id.state')
    state = fields.Selection([('draft', 'Draft'), ('done', 'Done'), ('cancel', 'Cancel')], string='State', copy=False,
                             default='draft')

    @api.model
    def create(self, vals):
        vals['no'] = "Order-" + self.env['ir.sequence'].get('spare.order.no.sequence')
        res = super(app_workshop_spare_order, self).create(vals)
        if res.state == 'draft':
            res.get_work_order_no()
        return res

    def set_draft(self):
        for rec in self:
            rec.state = 'draft'

    def set_done(self):
        for rec in self:
            sp_line_lst = []
            if rec.workshop_id:
                part_id = rec.workshop_id.partner_id.id
                type_id = rec.workshop_id.type_id.customer_pick_type
                origin_no = rec.workshop_id.no
                pick_dict = {
                    'workshop_id': rec.workshop_id.id,
                    'spare_order_id': rec.id,
                    'partner_id': part_id,
                    'picking_type_id': type_id.id,
                    'location_id': type_id.default_location_src_id.id,
                    'location_dest_id': type_id.default_location_dest_id.id, 'origin': origin_no}
                for spare in rec.spare_ids:
                    if spare.state == 'draft':
                        sp_line_lst.append((0, 0, {
                            'picking_type_id': type_id.id,
                            'location_id': type_id.default_location_src_id.id,
                            'location_dest_id': type_id.default_location_dest_id.id,
                            'product_id': spare.product_id.id,
                            'name': spare.product_id.name,
                            'product_uom_qty': spare.qty,
                            'product_uom': spare.product_id.uom_id.id
                        }))
                pick_dict['move_lines'] = sp_line_lst
                pick = self.env['stock.picking'].create(pick_dict)
                if pick:
                    rec.spare_ids.filtered(lambda x: x.state in ['draft'] and not x.pick_id).write({'pick_id': pick.id, 'state': 'done'})
                    rec.pick_id = pick.id
                    pick.action_confirm()
                    pick.action_assign()
                    pick.button_validate()
                    rec.state = 'done'

    def set_cancel(self):
        for rec in self:
            rec.state = 'cancel'


#########################################################################
######  workshop spare  ##########
#########################################################################

class app_workshop_spare(models.Model):
    _name = 'app.workshop.spare'
    _description = 'Workshop Spare Information'
    spare_order_id = fields.Many2one('app.workshop.spare.order', string='Spare Order', copy=False)
    workshop_id = fields.Many2one('app.workshop', string='Work-Order', related='spare_order_id.workshop_id')
    name = fields.Char(string='Description', copy=False, required=True)
    product_id = fields.Many2one('product.product', string='Spare', domain=[('type', '=', 'product')], copy=False,
                                 required=True)
    pick_id = fields.Many2one('stock.picking', string='Picking', copy=False)
    qty = fields.Float('Quantity', copy=False, default=1.00)
    price = fields.Float('Price', copy=False)
    wk_state = fields.Selection([('draft', 'Draft'), ('in_work', 'In Working'), ('done', 'Done'), ('cancel', 'Cancel')],
                                string='State', copy=False, default='draft', store=True, readonly=True,
                                related='workshop_id.state')
    state = fields.Selection([('draft', 'Draft'), ('done', 'Done'), ('cancel', 'Cancel')], string='State', copy=False,
                             default='draft')

    @api.onchange('product_id')
    def change_pro_id(self):
        for rec in self:
            if rec.product_id:
                rec.name = rec.product_id.name
                rec.price = rec.product_id.lst_price

    def set_draft(self):
        for rec in self:
            rec.state = 'draft'

    def set_done(self):
        for rec in self:
            rec.state = 'done'

    def set_cancel(self):
        for rec in self:
            rec.state = 'cancel'


#################################################################################################################
# Create the app.workshop.type model
#################################################################################################################

class app_move_type(models.Model):
    _name = 'app.workshop.type'
    _description = "Workshop Type"
    name = fields.Char('Name', required=True)
    vendor_pick_type = fields.Many2one('stock.picking.type', string='Vendor Picking Type', required=True)
    customer_pick_type = fields.Many2one('stock.picking.type', string='Customer Picking Type', required=True)
    a_loc = fields.Many2one('stock.location', 'Source Location')
    b_loc = fields.Many2one('stock.location', 'Destination Location')
    active = fields.Boolean('Active', default=True)
