# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import time
from odoo import models,api

tot = {}

class budget_report(models.AbstractModel):
    _name = 'report.om_account_budget.report_budget'

    @api.model
    def _get_report_values(self, docids, data=None):
        if not docids:
            docids = self.env.context.get('active_ids')
        model = self.env.context.get('active_model')
        model_id = self.env[model].browse(docids)
        return {
            'doc_ids': docids,
            'doc_model': model,
            'docs': model_id,
            'data': data,
            'funct': self.funct,
            'funct_total': self.funct_total,
            'time': time,
        }

    def funct(self, object, form, ids=None, done=None, level=1):
        if ids is None:
            ids = {}
        if not ids:
            ids = self.ids
        if not done:
            done = {}
        global tot
        tot = {
            'theo':0.00,
            'pln':0.00,
            'prac':0.00,
            'perc':0.00
        }
        result = []

        budgets = self.env['account.budget.post'].browse([object.id])
        c_b_lines_obj = self.env['crossovered.budget.lines']
        acc_analytic_obj = self.env['account.analytic.account']
        for budget_id in budgets:
            res = {}
            budget_ids = []
            d_from = form['date_from']
            d_to = form['date_to']

            for line in budget_id.crossovered_budget_line:
                budget_ids.append(line.id)

            if not budget_ids:
                return []
            self._cr.execute('SELECT DISTINCT(analytic_account_id) FROM crossovered_budget_lines WHERE id = ANY(%s)',(budget_ids,))
            an_ids = self._cr.fetchall()

            context = {'wizard_date_from': d_from, 'wizard_date_to': d_to}
            for i in range(0, len(an_ids)):
                if not an_ids[i][0]:
                    continue
                analytic_name = acc_analytic_obj.browse([an_ids[i][0]])
                res={
                    'b_id': '-1',
                    'a_id': '-1',
                    'name': analytic_name[0].name,
                    'status': 1,
                    'theo': 0.00,
                    'pln': 0.00,
                    'prac': 0.00,
                    'perc': 0.00
                }
                result.append(res)
                domain_lines = [('id', 'in', budget_ids),
                                ('analytic_account_id','=',an_ids[i][0]),
                                ('date_from', '<=', d_to),
                                ('date_to', '>=', d_from)]
                line_ids = c_b_lines_obj.search(domain_lines)
                #line_id = c_b_lines_obj.browse(line_ids)
                tot_theo = tot_pln = tot_prac = tot_perc = 0.00

                done_budget = []
                for line in line_ids:
                    if line.id in budget_ids:
                        theo = pract = 0.00
                        theo = c_b_lines_obj._theo_amt([line.id])[line.id]
                        pract = c_b_lines_obj._prac_amt([line.id])[line.id]
                        if line.general_budget_id.id in done_budget:
                            for record in result:
                                if record['b_id'] == line.general_budget_id.id  and record['a_id'] == line.analytic_account_id.id:
                                    record['theo'] += theo
                                    record['pln'] += line.planned_amount
                                    record['prac'] += pract
                                    if record['theo'] != 0.00:
                                        perc = (record['prac'] / record['theo']) * 100
                                    else:
                                        perc = 0.00
                                    record['perc'] = perc
                                    tot_theo += theo
                                    tot_pln += line.planned_amount
                                    tot_prac += pract
                                    tot_perc += perc
                        else:
                            if theo != 0.00:
                                perc = (pract / theo) * 100
                            else:
                                perc = 0.00
                            res1 = {
                                    'a_id': line.analytic_account_id.id,
                                    'b_id': line.general_budget_id.id,
                                    'name': line.general_budget_id.name,
                                    'status': 2,
                                    'theo': theo,
                                    'pln': line.planned_amount,
                                    'prac': pract,
                                    'perc': perc,
                            }
                            tot_theo += theo
                            tot_pln += line.planned_amount
                            tot_prac += pract
                            tot_perc += perc
                            if form['report'] == 'analytic-full':
                                result.append(res1)
                                done_budget.append(line.general_budget_id.id)
                    else:

                        if line.general_budget_id.id in done_budget:
                            continue
                        else:
                            res1={
                                    'a_id': line.analytic_account_id.id,
                                    'b_id': line.general_budget_id.id,
                                    'name': line.general_budget_id.name,
                                    'status': 2,
                                    'theo': 0.00,
                                    'pln': 0.00,
                                    'prac': 0.00,
                                    'perc': 0.00
                            }
                            if form['report'] == 'analytic-full':
                                result.append(res1)
                                done_budget.append(line.general_budget_id.id)
                if tot_theo == 0.00:
                    tot_perc = 0.00
                else:
                    tot_perc = float(tot_prac / tot_theo) * 100
                if form['report'] == 'analytic-full':
                    result[-(len(done_budget) +1)]['theo'] = tot_theo
                    tot['theo'] += tot_theo
                    result[-(len(done_budget) +1)]['pln'] = tot_pln
                    tot['pln'] += tot_pln
                    result[-(len(done_budget) +1)]['prac'] = tot_prac
                    tot['prac'] += tot_prac
                    result[-(len(done_budget) +1)]['perc'] = tot_perc
                else:
                    result[-1]['theo'] = tot_theo
                    tot['theo'] += tot_theo
                    result[-1]['pln'] = tot_pln
                    tot['pln'] += tot_pln
                    result[-1]['prac'] = tot_prac
                    tot['prac'] += tot_prac
                    result[-1]['perc'] = tot_perc
            if tot['theo'] == 0.00:
                tot['perc'] = 0.00
            else:
                tot['perc'] = float(tot['prac'] / tot['theo']) * 100
        return result

    def funct_total(self, form):
        result = []
        res = {}
        res = {
             'tot_theo': tot['theo'],
             'tot_pln': tot['pln'],
             'tot_prac': tot['prac'],
             'tot_perc': tot['perc']
        }
        result.append(res)
        return result


# class report_budget(osv.AbstractModel):
#     _name = 'report.account_budget.report_budget'
#     _inherit = 'report.abstract_report'
#     _template = 'account_budget.report_budget'
#     _wrapped_report_class = budget_report
