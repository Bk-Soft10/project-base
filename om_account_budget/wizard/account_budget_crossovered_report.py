# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import time
from odoo import models,fields


class account_budget_crossvered_report(models.TransientModel):

    _name = "account.budget.crossvered.report"
    _description = "Account Budget crossovered report"
    date_from = fields.Date('Start of period',default=lambda *a: time.strftime('%Y-01-01'), required=True)
    date_to = fields.Date('End of period',default=lambda *a: time.strftime('%Y-%m-%d'), required=True)

    def check_report(self):
        data = self.read()[0]
        datas = {
            'ids': self.ids,
            'model': 'crossovered.budget',
            'form': data
        }
        datas['form']['ids'] = datas['ids']
        datas['form']['report'] = 'analytic-full'
        return self.env.ref('om_account_budget.action_report_crossovered_budget').report_action(self, data=datas)
