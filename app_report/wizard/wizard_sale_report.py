# -*- coding: utf-8 -*-
import time
from datetime import datetime, timedelta, date
from dateutil import relativedelta
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError



class WizSoReport(models.TransientModel):
    _name = 'wiz.so.report.app'
    _description = 'Wizard SO Report'

    date_from = fields.Date('F-Date', default=time.strftime('%Y-%m-01'), required=True)
    date_to = fields.Date('T-Date',
                          default=str(datetime.now() + relativedelta.relativedelta(months=+1, day=1, days=-1))[:10],
                          required=True)
    partner_ids = fields.Many2many('res.partner', string='Customers')
    product_ids = fields.Many2many('product.product', string='Products')
    status = fields.Selection([
        ('all', 'All'),
        ('order', 'Ordered'),
    ], string='Status', required=True, default='all')
    group_by = fields.Selection([
        ('product', 'Products'),
        ('partner', 'Customers'),
    ], string='Group By', required=True, default='product')
    report_type = fields.Selection([
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
    ], string='Report Type', required=True, default='pdf')

    def print_report(self):
        if self.report_type == 'pdf' or not self.report_type:
            data = self.read(['date_from', 'date_to', 'group_by', 'report_type', 'status', 'partner_ids', 'product_ids'])[0]
            return self.env.ref('app_report.action_so_report').report_action(self, data=data)
        else:
            pass
