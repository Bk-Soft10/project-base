# -*- coding: utf-8 -*-

import time
from odoo import api, models, _
from odoo.exceptions import UserError


class AccountReport(models.AbstractModel):
    _name = 'report.app_financial_report.view_account_report'

    def _compute_account_op_balance(self, accounts):
        mapping = {
            'op_balance': "COALESCE(SUM(debit),0) - COALESCE(SUM(credit), 0) as op_balance",
            'op_debit': "COALESCE(SUM(debit), 0) as op_debit",
            'op_credit': "COALESCE(SUM(credit), 0) as op_credit",
        }

        res = {}
        for account in accounts:
            res[account.id] = dict.fromkeys(mapping, 0.0)
        if accounts:
            tables, where_clause, where_params = self.env['account.move.line'].with_context(initial_bal=True, date_to=False)._query_get()
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

    def _compute_partner_op_balance(self, partners):
        mapping = {
            'op_balance': "COALESCE(SUM(debit),0) - COALESCE(SUM(credit), 0) as op_balance",
            'op_debit': "COALESCE(SUM(debit), 0) as op_debit",
            'op_credit': "COALESCE(SUM(credit), 0) as op_credit",
        }

        res = {}
        for partner in partners:
            res[partner.id] = dict.fromkeys(mapping, 0.0)
        if partners:
            tables, where_clause, where_params = self.env['account.move.line'].with_context(initial_bal=True, date_to=False)._query_get()
            tables = tables.replace('"', '') if tables else "account_move_line"
            wheres = [""]
            if where_clause.strip():
                wheres.append(where_clause.strip())
            filters = " AND ".join(wheres)
            request = "SELECT partner_id as id, " + ', '.join(mapping.values()) + \
                      " FROM " + tables + \
                      " WHERE partner_id IN %s " \
                      + filters + \
                      " GROUP BY partner_id"
            params = (tuple(partners._ids),) + tuple(where_params)
            self.env.cr.execute(request, params)
            for row in self.env.cr.dictfetchall():
                res[row['id']] = row
        return res

    def _compute_partner_balance(self, partners):
        mapping = {
            'balance': "COALESCE(SUM(debit),0) - COALESCE(SUM(credit), 0) as balance",
            'debit': "COALESCE(SUM(debit), 0) as debit",
            'credit': "COALESCE(SUM(credit), 0) as credit",
        }

        res = {}
        for partner in partners:
            res[partner.id] = dict.fromkeys(mapping, 0.0)
        if partners:
            tables, where_clause, where_params = self.env['account.move.line']._query_get()
            tables = tables.replace('"', '') if tables else "account_move_line"
            wheres = [""]
            if where_clause.strip():
                wheres.append(where_clause.strip())
            filters = " AND ".join(wheres)
            request = "SELECT partner_id as id, " + ', '.join(mapping.values()) + \
                      " FROM " + tables + \
                      " WHERE account_id IN %s " \
                      + filters + \
                      " GROUP BY partner_id"
            params = (tuple(partners._ids),) + tuple(where_params)
            self.env.cr.execute(request, params)
            for row in self.env.cr.dictfetchall():
                res[row['id']] = row
        return res

    def update_accounts_bal_values(self, op_bal, account_ids):
        bal_vals = self._compute_account_balance(account_ids)
        if op_bal == True:
            op_bal_vals = self._compute_account_op_balance(account_ids)
            for key in bal_vals:
                if key in op_bal_vals:
                    bal_vals[key].update(op_bal_vals[key])
                    bal_vals[key]['fn_balance'] = bal_vals[key].get('balance', 0) + bal_vals[key].get('op_balance', 0)
                    bal_vals[key]['fn_debit'] = bal_vals[key].get('debit', 0) + bal_vals[key].get('op_debit', 0)
                    bal_vals[key]['fn_credit'] = bal_vals[key].get('credit', 0) + bal_vals[key].get('op_credit', 0)
        for key in bal_vals:
            account_rec = self.env['account.account'].browse([key])
            bal_vals[key]['account_name'] = account_rec.display_name if account_rec else str(key)
        return bal_vals

    def update_partners_bal_values(self, op_bal, partner_ids):
        bal_vals = self._compute_partner_balance(partner_ids)
        if op_bal == True:
            op_bal_vals = self._compute_partner_op_balance(partner_ids)
            for key in bal_vals:
                if key in op_bal_vals:
                    bal_vals[key].update(op_bal_vals[key])
                    bal_vals[key]['fn_balance'] = bal_vals[key].get('balance', 0) + bal_vals[key].get('op_balance', 0)
                    bal_vals[key]['fn_debit'] = bal_vals[key].get('debit', 0) + bal_vals[key].get('op_debit', 0)
                    bal_vals[key]['fn_credit'] = bal_vals[key].get('credit', 0) + bal_vals[key].get('op_credit', 0)
        for key in bal_vals:
            partner_rec = self.env['res.partner'].browse([key])
            bal_vals[key]['partner_name'] = partner_rec.display_name if partner_rec else str(key)
        return bal_vals

    def get_account_lines(self, wizard, data):
        lines = []
        val_lines = {}
        if wizard.group_by == 'account':
            account_ids = wizard.account_ids
            if not account_ids:
                account_ids = self.env['account.account'].search([])
            val_lines = self.update_accounts_bal_values(wizard.opening_balance, account_ids)
        if wizard.group_by == 'partner':
            partner_ids = wizard.partner_ids
            if not partner_ids:
                partner_ids = self.env['res.partner'].search([])
            val_lines = self.update_partners_bal_values(wizard.opening_balance, partner_ids)
        print("val_lines ", val_lines)
        lines = [item for item in val_lines.values()]
        print("lines ", lines)
        return lines

    @api.model
    def _get_report_values(self, docids, data=None):
        model = self.env.context.get('active_model')
        docs = self.env[model].sudo().browse(self.env.context.get('active_id'))
        report_lines = self.get_account_lines(docs, data.get('form'))
        return {
            'doc_ids': self.ids,
            'doc_model': model,
            'data': data,
            'docs': docs,
            'report_line_val': report_lines,
        }
