# -*- coding: utf-8 -*-
import time
from datetime import datetime, timedelta, date
from dateutil import relativedelta
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError



class WizStockReport(models.TransientModel):
    _name = 'wiz.stock.report.app'
    _description = 'Wizard Stock Report'

    date_from = fields.Date('F-Date', default=time.strftime('%Y-%m-01'), required=True)
    date_to = fields.Date('T-Date',
                          default=str(datetime.now() + relativedelta.relativedelta(months=+1, day=1, days=-1))[:10],
                          required=True)
    opening_balance = fields.Boolean('Opening Balance')
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse')
    location_ids = fields.Many2many('stock.location', string='Locations')
    product_ids = fields.Many2many('product.product', string='Products')
    status = fields.Selection([
        ('all', 'All'),
        ('done', 'Confirmed'),
    ], string='Status', required=True, default='all')
    report_type = fields.Selection([
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
    ], string='Report Type', required=True, default='pdf')

    def print_report(self):
        if self.report_type == 'pdf' or not self.report_type:
            data = self.read(['date_from', 'date_to', 'opening_balance', 'warehouse_id', 'report_type', 'status', 'location_ids', 'product_ids'])[0]
            return self.env.ref('app_report.action_stock_report').report_action(self, data=data)
        else:
            pass
