# -*- coding: utf-8 -*-
import time
from datetime import datetime, timedelta, date
from dateutil import relativedelta
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError



class WizLedgerReport(models.TransientModel):
    _name = 'wiz.account.report'
    _description = 'Wizard Account Report'

    date_from = fields.Date('F-Date', default=time.strftime('%Y-%m-01'), required=False)
    date_to = fields.Date('T-Date', default=str(datetime.now() + relativedelta.relativedelta(months=+1, day=1, days=-1))[:10],
                          required=False)
    reconciled = fields.Boolean('Reconciled Entries')
    opening_balance = fields.Boolean('Opening Balance')
    without_zero = fields.Boolean('Without Zero Balance')
    show_summary = fields.Boolean(string='Show Details')
    partner_ids = fields.Many2many('res.partner', string='Partners')
    account_ids = fields.Many2many('account.account', string='Accounts')
    debit_credit = fields.Boolean(string='Display Debit/Credit Columns', help="This option allows you to get more details about the way your balances are computed. Because it is space consuming, we do not allow to use it while doing a comparison.")
    group_by = fields.Selection([
        ('account', 'Accounts'),
        ('partner', 'Partners'),
    ], string='Group By', required=True, default='account')
    partner_type = fields.Selection([
        ('receivable', 'Receivable'),
        ('payable', 'Payable'),
        ('all', 'All Partner'),
    ], string='Partner Type', default='all')
    target_move = fields.Selection([
        ('all', 'All'),
        ('posted', 'Posted'),
    ], string='Target', required=True, default='posted')
    report_type = fields.Selection([
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
    ], string='Report Type', required=True, default='pdf')

    def print_report(self):
        if self.report_type == 'pdf' or not self.report_type:
            data = self.read(['reconciled', 'date_from', 'date_to', 'opening_balance', 'report_type', 'target_move', 'debit_credit', 'without_zero', 'group_by', 'partner_ids', 'account_ids', 'show_summary', 'partner_type'])[0]
            return self.env.ref('app_financial_report.action_account_report').report_action(self, data=data)
        else:
            data = self.read(['reconciled', 'date_from', 'date_to', 'opening_balance', 'report_type', 'target_move', 'debit_credit', 'without_zero', 'group_by', 'partner_ids', 'account_ids', 'show_summary', 'partner_type'])[0]
            return self.env.ref('app_financial_report.report_ledger_xlsx').with_context(landscape=True).report_action(self, data=data)
