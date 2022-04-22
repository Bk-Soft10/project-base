# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import time
from odoo import fields, models


class account_budget_crossvered_summary_report(models.TransientModel):
    """
    This wizard provides the crossovered budget summary report'
    """
    _name = 'account.budget.crossvered.summary.report'
    _description = 'Account Budget crossovered summary report'
    date_from = fields.Date('Start of period',default=lambda *a: time.strftime('%Y-01-01'), required=True)
    date_to = fields.Date('End of period',default=lambda *a: time.strftime('%Y-%m-%d'), required=True)

    def check_report(self):
        if self._context is None:
            context = {}
        data = self.read()[0]
        datas = {
            'ids': self.ids,
            'model': 'crossovered.budget',
            'form': data
        }
        datas['form']['ids'] = datas['ids']
        datas['form']['report'] = 'analytic-one'
        return self.env.ref('om_account_budget.action_report_crossovered_budget').report_action(self, data=datas)
