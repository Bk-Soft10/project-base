# -*- coding: utf-8 -*-
#############################################################################
#
#############################################################################

import time
from odoo import api, models, fields, _
from odoo.exceptions import UserError


class ReportFinancial(models.AbstractModel):
    _name = 'report.app_financial_report.report_financial'

    def _compute_account_balance(self, accounts):
        mapping = {
            'balance': "COALESCE(SUM(debit),0) - COALESCE(SUM(credit), 0) as balance",
            'debit': "COALESCE(SUM(debit), 0) as debit",
            'credit': "COALESCE(SUM(credit), 0) as credit",
        }

        res = {}
        for account in accounts:
            res[account.id] = dict.fromkeys(mapping, 0.0)
        if accounts:
            tables, where_clause, where_params = self.env['account.move.line']._query_get()
            tables = tables.replace('"', '') if tables else "account_move_line"
            wheres = [""]
            if where_clause.strip():
                wheres.append(where_clause.strip())
            filters = " AND ".join(wheres)
            request = "SELECT account_id as id, " + ', '.join(mapping.values()) + \
                      " FROM " + tables + \
                      " WHERE account_id IN %s " \
                      + filters + \
                      " GROUP BY account_id"
            params = (tuple(accounts._ids),) + tuple(where_params)
            self.env.cr.execute(request, params)
            for row in self.env.cr.dictfetchall():
                res[row['id']] = row
        return res

    def _compute_report_balance(self, reports):

        res = {}
        fields = ['credit', 'debit', 'balance']
        for report in reports:
            if report.id in res:
                continue
            res[report.id] = dict((fn, 0.0) for fn in fields)
            if report.type == 'account_type':
                # it's the sum the leaf accounts with such an account type
                accounts = self.env['account.account'].search([('user_type_id', 'in', report.account_type_ids.ids)])
                res[report.id]['account'] = self._compute_account_balance(accounts)
                for value in res[report.id]['account'].values():
                    for field in fields:
                        res[report.id][field] += value.get(field)
            elif report.type == 'account_report' and report.account_report_id:
                # it's the amount of the linked
                #res[report.id]['account'] = self._compute_report_balance(report.account_report_id)
                res[report.id]['account'] = self._compute_account_balance(report.account_report_id.account_ids)
                for value in res[report.id]['account'].values():
                    for field in fields:
                        res[report.id][field] += value.get(field)
                res[report.id]['account'] = False
            elif report.type == 'accounts':
                # it's the amount of the linked
                res[report.id]['account'] = self._compute_account_balance(report.account_ids)
                for value in res[report.id]['account'].values():
                    for field in fields:
                        res[report.id][field] += value.get(field)

            elif report.type == 'sum':
                # it's the sum of the linked accounts
                accc_idds = self.get_acc_group_root(report)
                res[report.id]['account'] = self._compute_account_balance(accc_idds)
                for values in res[report.id]['account'].values():
                    for field in fields:
                        res[report.id][field] += values.get(field)
                res[report.id]['account'] = False
        return res

    def get_acc_group_root(self,group):
        account_ids = self.env['account.account']
        if group.type == 'sum':
            for group_child_id in group._get_children_by_order():
                if group_child_id.type == 'accounts':
                    account_ids += group_child_id.account_ids
                if group_child_id.type == 'account_type':
                    account_ids += self.env['account.account'].search([('user_type_id.id','in',group_child_id.account_type_ids.ids)])
        if group.type == 'account_report':
            for group_child_id in group._get_children_by_order():
                if group_child_id.type == 'accounts':
                    account_ids += group_child_id.account_ids
                if group_child_id.type == 'account_type':
                    account_ids += self.env['account.account'].search([('user_type_id.id','in',group_child_id.account_type_ids.ids)])
        return account_ids

    def get_account_lines(self, data):
        lines = []
        account_report = self.env['account.financial.report'].search([('id', '=', data['account_report_id'][0])])
        child_reports = account_report._get_children_by_order()
        res = self.with_context(data.get('used_context'))._compute_report_balance(child_reports)
        if data['enable_filter']:
            comparison_res = self.with_context(data.get('comparison_context'))._compute_report_balance(child_reports)
            for report_id, value in comparison_res.items():
                res[report_id]['comp_bal'] = value['balance']
                report_acc = res[report_id].get('account')
                if report_acc:
                    for account_id, val in comparison_res[report_id].get('account').items():
                        report_acc[account_id]['comp_bal'] = val['balance']

        for report in child_reports:
            vals = {
                'name': report.name,
                'balance': res[report.id]['balance'] * float(report.sign) if report.sign else 1,
                'type': 'report',
                'level': bool(report.style_overwrite) and int(report.style_overwrite) or report.level,
                'account_type': report.type or False,
            }
            if data['debit_credit']:
                vals['debit'] = res[report.id]['debit']
                vals['credit'] = res[report.id]['credit']

            if data['enable_filter']:
                vals['balance_cmp'] = res[report.id]['comp_bal'] * float(report.sign) if report.sign else 1

            lines.append(vals)
            if report.display_detail == 'no_detail':
                # the rest of the loop is used to display the details of the financial report, so it's not needed here.
                continue
            if res[report.id].get('account'):
                # if res[report.id].get('debit'):
                sub_lines = []
                print("acc res ff ",res[report.id])
                for account_id, value in res[report.id]['account'].items():
                    # if there are accounts to display, we add them to the lines with a level equals to their level in
                    # the COA + 1 (to avoid having them with a too low level that would conflicts with the level of data
                    # financial reports for Assets, liabilities...)
                    flag = False
                    account = self.env['account.account'].browse(account_id)

                    vals = {
                        'name': account.code + ' ' + account.name,
                        'balance': value['balance'] * float(report.sign) if report.sign else 1,
                        'type': 'account',
                        'level': report.display_detail == 'detail_with_hierarchy' and 4,
                        'account_type': account.internal_type,
                    }
                    if data['debit_credit']:
                        vals['debit'] = value['debit']
                        vals['credit'] = value['credit']
                        if not account.company_id.currency_id.is_zero(
                                vals['debit']) or not account.company_id.currency_id.is_zero(vals['credit']):
                            flag = True
                    if not account.company_id.currency_id.is_zero(vals['balance']):
                        flag = True
                    if data['enable_filter']:
                        vals['balance_cmp'] = value['comp_bal'] * float(report.sign) if report.sign else 1
                        if not account.company_id.currency_id.is_zero(vals['balance_cmp']):
                            flag = True
                    if flag:
                        sub_lines.append(vals)
                lines += sorted(sub_lines, key=lambda sub_line: sub_line['name'])
        print(lines)
        return lines

    @api.model
    def _get_report_values(self, docids, data=None):
        print('success')
        if not data.get('form') or not self.env.context.get('active_model') or not self.env.context.get('active_id'):
            raise UserError(_("Form content is missing, this report cannot be printed."))

        self.model = self.env.context.get('active_model')
        docs = self.env[self.model].browse(self.env.context.get('active_id'))
        report_lines = self.get_account_lines(data.get('form'))
        return {
            'doc_ids': self.ids,
            'doc_model': self.model,
            'data': data['form'],
            'docs': docs,
            'time': time,
            'get_account_lines': report_lines,
        }


class AccountAccount(models.Model):
    _inherit = 'account.account'

    # def get_cash_flow_ids(self):
    #     cash_flow_id = self.env.ref('app_financial_report.account_financial_report_cash_flow0')
    #     if cash_flow_id:
    #         return [('parent_id.id', '=', cash_flow_id.id)]
    #
    # cash_flow_type = fields.Many2one('account.financial.report', string="Cash Flow type", domain=get_cash_flow_ids)

    cash_flow_type = fields.Many2one('account.financial.report', string="Cash Flow type")

    @api.onchange('cash_flow_type')
    def onchange_cash_flow_type(self):
        print(self._origin.id, "self.cash_flow_type", self._origin.cash_flow_type)

        for rec in self.cash_flow_type:
            print('rec', rec)
            # update new record
            rec.write({
                'account_ids': [(4, self._origin.id)]
            })

        if self._origin.cash_flow_type.ids:
            for rec in self._origin.cash_flow_type:
                print('delete', rec.name)
                # remove old record
                rec.write({
                    'account_ids': [(3, self._origin.id)]
                })
