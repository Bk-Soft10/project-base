    # -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import time
from odoo import fields, models


class account_budget_analytic(models.TransientModel):

    _name = 'account.budget.analytic'
    _description = 'Account Budget report for analytic account'
    date_from = fields.Date('Start of period',default=lambda *a: time.strftime('%Y-01-01'), required=True)
    date_to = fields.Date('End of period', default=lambda *a: time.strftime('%Y-%m-%d'), required=True)

    def check_report(self):
        if self._context is None:
            context = {}
        data = self.read()[0]
        datas = {
            'ids': self.ids,
            'model': 'account.analytic.account',
            'form': data
        }
        datas['form']['ids'] = datas['ids']
        return self.env.ref('om_account_budget.action_report_analytic_account_budget').report_action(self, data=datas)