# -*- coding: utf-8 -*-

import time
from odoo import api, models, _
from odoo.exceptions import UserError
import time
from datetime import datetime, timedelta, date
from dateutil import relativedelta


class AccountReport(models.AbstractModel):
    _name = 'report.app_financial_report.view_account_report'

    def getFilterdValue(self, wizard, account_ids):
        query_where = "where m_line.move_id = m.id "

        if account_ids:
            if (len(account_ids) == 1):
                query_where += " and m_line.account_id = %s " % (account_ids[0])
            else:
                query_where += " and m_line.account_id IN %s " % (tuple(account_ids),)

        query_where += self.where_sql(wizard, False)

        query_all = """
        SELECT m_line.account_id as account_id,
        SUM(m_line.debit) as debit,
        SUM(m_line.credit) as credit,
        (SUM(m_line.debit)-SUM(m_line.credit)) as balance
        FROM account_move_line m_line
        JOIN account_move m ON
        m_line.move_id = m.id
        """
        if query_where:
            query_all = query_all + query_where + " group by m_line.account_id "
        else:
            query_all = query_all + " group by m_line.account_id "

        self.env.cr.execute(query_all)

        result = self.env.cr.dictfetchall() or False
        result2 = {}
        for row in result:
            result2[row['account_id']] = row
        return result2

    def date_str(self, date):
        return datetime.strftime(date, '%Y-%m-%d')

    def where_sql(self, wizard, op_balance):
        whare_str = " AND m_line.parent_state != 'cancel'"
        if op_balance:
            if wizard.date_from:
                whare_str = " AND m_line.date < '" + self.date_str(wizard.date_from) + "' "
        else:
            if wizard.date_from:
                whare_str += " AND m_line.date >= '" + self.date_str(wizard.date_from) + "' "
            if wizard.date_to:
                whare_str += " AND m_line.date <= '" + self.date_str(wizard.date_to) + "' "

        if wizard.target_move == 'posted':
            whare_str += " AND m_line.parent_state in ('posted') "
        return whare_str

    def _compute_account_op_balance(self, wizard, accounts):
        query_where = "where m_line.move_id = m.id "
        account_ids = accounts.ids or []
        if account_ids:
            if (len(account_ids) == 1):
                query_where += " and m_line.account_id = %s " % (account_ids[0])
            else:
                query_where += " and m_line.account_id IN %s " % (tuple(account_ids),)

        query_where += self.where_sql(wizard, True)

        query_all = """
                SELECT m_line.account_id as account_id,
                acc.code as account_code,
                SUM(m_line.debit) as op_debit,
                SUM(m_line.credit) as op_credit,
                (SUM(m_line.debit)-SUM(m_line.credit)) as op_balance
                FROM account_move_line m_line
                JOIN account_move m ON
                m_line.move_id = m.id
                JOIN account_account acc ON
                m_line.account_id = acc.id
                """
        if query_where:
            query_all = query_all + query_where + " group by acc.code,m_line.account_id order by acc.code,m_line.account_id "
        else:
            query_all = query_all + " group by acc.code,m_line.account_id order by acc.code,m_line.account_id "

        self.env.cr.execute(query_all)

        result = self.env.cr.dictfetchall()
        result2 = {}
        for row in result:
            result2[row['account_id']] = row
        if not result:
            for key in account_ids:
                result2[key] = {'account_id': key, 'op_debit': 0, 'op_credit': 0, 'op_balance': 0}
        return result2

    def _compute_account_balance(self, wizard, accounts):
        query_where = "where m_line.move_id = m.id "
        account_ids = accounts.ids or []
        if account_ids:
            if len(account_ids) == 1:
                query_where += " and m_line.account_id = %s " % (account_ids[0])
            else:
                query_where += " and m_line.account_id IN %s " % (tuple(account_ids),)

        query_where += self.where_sql(wizard, False)

        query_all = """
                SELECT m_line.account_id as account_id,
                acc.code as account_code,
                SUM(m_line.debit) as debit,
                SUM(m_line.credit) as credit,
                (SUM(m_line.debit)-SUM(m_line.credit)) as balance
                FROM account_move_line m_line
                JOIN account_move m ON
                m_line.move_id = m.id
                JOIN account_account acc ON
                m_line.account_id = acc.id
                """
        if query_where:
            query_all = query_all + query_where + " group by acc.code,m_line.account_id order by acc.code,m_line.account_id "
        else:
            query_all = query_all + " group by acc.code,m_line.account_id order by acc.code,m_line.account_id "

        self.env.cr.execute(query_all)

        result = self.env.cr.dictfetchall()
        mv_lines = self._compute_account_balance_summary(wizard, accounts)
        result2 = {}
        for row in result:
            lines = [mv_line for mv_line in mv_lines if 'account_id' in mv_line and mv_line['account_id'] == row['account_id']]
            row.update(lines=lines)
            result2[row['account_id']] = row
        if not result:
            for key in account_ids:
                result2[key] = {'account_id': key, 'debit': 0, 'credit': 0, 'balance': 0, 'lines': []}
        return result2

    def _compute_account_balance_summary(self, wizard, accounts):
        query_where = "where m_line.move_id = m.id "
        account_ids = accounts.ids or []
        if account_ids:
            if len(account_ids) == 1:
                query_where += " and m_line.account_id = %s " % (account_ids[0])
            else:
                query_where += " and m_line.account_id IN %s " % (tuple(account_ids),)

        query_where += self.where_sql(wizard, False)

        query_all = """
                SELECT m_line.account_id as account_id,
                acc.code as account_code,
                m_line.date,
                m_line.ref,
                j.code,
                m_line.debit,
                m_line.credit,
                (m_line.debit-m_line.credit) as balance
                FROM account_move_line m_line
                JOIN account_move m ON
                m_line.move_id = m.id
                JOIN account_account acc ON
                m_line.account_id = acc.id
                JOIN account_journal j ON
                m_line.journal_id = j.id
                """
        if query_where:
            query_all = query_all + query_where + " order by m_line.date "
        else:
            query_all = query_all + " order by m_line.date "

        self.env.cr.execute(query_all)

        result = self.env.cr.dictfetchall() or []
        # result2 = {}
        # for row in result:
        #     result2[row['account_id']] = row
        # if not result:
        #     for key in account_ids:
        #         result2[key] = {'account_id': key, 'debit': 0, 'credit': 0, 'balance': 0, 'date': False, 'ref': '', 'journal_code': ''}
        return result

    def _where_partner_accounts(self, wizard, partners):
        query_where = ' '
        receivable_accounts = partners.mapped('property_account_receivable_id').ids or []
        payable_accounts = partners.mapped('property_account_payable_id').ids or []
        partner_accounts = receivable_accounts + payable_accounts
        if wizard.partner_type in ['receivable'] and receivable_accounts:
            if len(receivable_accounts) == 1:
                query_where += " AND act.type IN ('receivable') AND m_line.account_id = %s " % (receivable_accounts[0])
            else:
                query_where += " AND act.type IN ('receivable') AND m_line.account_id IN %s " % (tuple(receivable_accounts),)
        elif wizard.partner_type in ['payable'] and payable_accounts:
            if len(payable_accounts) == 1:
                query_where += " AND act.type IN ('payable') AND m_line.account_id = %s " % (payable_accounts[0])
            else:
                query_where += " AND act.type IN ('payable') AND m_line.account_id IN %s " % (tuple(payable_accounts),)
        elif receivable_accounts and payable_accounts and partner_accounts:
            if len(partner_accounts) == 1:
                query_where += " AND act.type IN ('receivable', 'payable') AND m_line.account_id = %s " % (partner_accounts[0])
            else:
                query_where += " AND act.type IN ('receivable', 'payable') AND m_line.account_id IN %s " % (tuple(partner_accounts),)
        return query_where

    def _compute_partner_op_balance(self, wizard, partners):
        query_where = "WHERE m_line.move_id = m.id "
        query_where += self._where_partner_accounts(wizard, partners) or ''
        partner_ids = partners.ids or []

        if partner_ids:
            if (len(partner_ids) == 1):
                query_where += " and m_line.partner_id = %s " % (partner_ids[0])
            else:
                query_where += " and m_line.partner_id IN %s " % (tuple(partner_ids),)

        query_where += self.where_sql(wizard, True)

        query_all = """
                SELECT m_line.partner_id as partner_id,
                SUM(m_line.debit) as op_debit,
                SUM(m_line.credit) as op_credit,
                (SUM(m_line.debit)-SUM(m_line.credit)) as op_balance
                FROM account_move_line m_line
                JOIN account_move m ON m_line.move_id = m.id
                LEFT JOIN account_account a ON (m_line.account_id=a.id)
                LEFT JOIN account_account_type act ON (a.user_type_id=act.id)
                LEFT JOIN res_partner r_partner ON (m_line.partner_id=r_partner.id)
                """
        if query_where:
            query_all = query_all + query_where + " group by m_line.partner_id "
        else:
            query_all = query_all + " group by m_line.partner_id "

        self.env.cr.execute(query_all)

        result = self.env.cr.dictfetchall()
        result2 = {}
        for row in result:
            result2[row['partner_id']] = row
        if not result:
            for key in partner_ids:
                result2[key] = {'partner_id': key, 'op_debit': 0, 'op_credit': 0, 'op_balance': 0}
        return result2

    def _compute_partner_balance(self, wizard, partners):
        query_where = "WHERE m_line.move_id = m.id "
        query_where += self._where_partner_accounts(wizard, partners) or ''
        partner_ids = partners.ids or []

        if partner_ids:
            if (len(partner_ids) == 1):
                query_where += " and m_line.partner_id = %s " % (partner_ids[0])
            else:
                query_where += " and m_line.partner_id IN %s " % (tuple(partner_ids),)

        query_where += self.where_sql(wizard, False)

        query_all = """
                SELECT m_line.partner_id as partner_id,
                SUM(m_line.debit) as debit,
                SUM(m_line.credit) as credit,
                (SUM(m_line.debit)-SUM(m_line.credit)) as balance
                FROM account_move_line m_line
                JOIN account_move m ON m_line.move_id = m.id
                LEFT JOIN account_account a ON (m_line.account_id=a.id)
                LEFT JOIN account_account_type act ON (a.user_type_id=act.id)
                LEFT JOIN res_partner r_partner ON (m_line.partner_id=r_partner.id)
                """
        if query_where:
            query_all = query_all + query_where + " group by m_line.partner_id "
        else:
            query_all = query_all + " group by m_line.partner_id "

        self.env.cr.execute(query_all)

        result = self.env.cr.dictfetchall()
        mv_lines = self._compute_partner_balance_summary(wizard, partners)
        result2 = {}
        for row in result:
            lines = [mv_line for mv_line in mv_lines if 'partner_id' in mv_line and mv_line['partner_id'] == row['partner_id']]
            row.update(lines=lines)
            result2[row['partner_id']] = row
        if not result:
            for key in partner_ids:
                result2[key] = {'partner_id': key, 'debit': 0, 'credit': 0, 'balance': 0, 'lines': []}
        return result2

    def _compute_partner_balance_summary(self, wizard, partners):
        query_where = "WHERE m_line.move_id = m.id "
        query_where += self._where_partner_accounts(wizard, partners) or ''
        partner_ids = partners.ids or []

        if partner_ids:
            if (len(partner_ids) == 1):
                query_where += " and m_line.partner_id = %s " % (partner_ids[0])
            else:
                query_where += " and m_line.partner_id IN %s " % (tuple(partner_ids),)

        query_where += self.where_sql(wizard, False)

        query_all = """
                SELECT m_line.partner_id,
                m_line.date,
                m_line.ref,
                j.code,
                m_line.debit,
                m_line.credit,
                (m_line.debit-m_line.credit) as balance
                FROM account_move_line m_line
                JOIN account_move m ON m_line.move_id = m.id
                JOIN account_journal j ON m_line.journal_id = j.id
                LEFT JOIN account_account a ON (m_line.account_id=a.id)
                LEFT JOIN account_account_type act ON (a.user_type_id=act.id)
                LEFT JOIN res_partner r_partner ON (m_line.partner_id=r_partner.id)
                """
        if query_where:
            query_all = query_all + query_where + " order by m_line.date "
        else:
            query_all = query_all + " order by m_line.date "

        self.env.cr.execute(query_all)

        result = self.env.cr.dictfetchall()
        # result2 = {}
        # for row in result:
        #     result2[row['partner_id']] = row
        # if not result:
        #     for key in partner_ids:
        #         result2[key] = {'partner_id': key, 'debit': 0, 'credit': 0, 'balance': 0, 'date': False, 'ref': '', 'journal_code': ''}
        return result

    def update_accounts_bal_values(self, wizard, op_bal, account_ids):
        bal_vals = self._compute_account_balance(wizard, account_ids)
        # bal_vals = self.getFilterdValue(wizard, account_ids.ids)

        val_ids = [id for id in bal_vals]
        for item in account_ids.ids:
            if item not in val_ids:
                bal_vals[item] = {'account_id': item, 'debit': 0, 'credit': 0, 'balance': 0}

        if op_bal == True:
            op_bal_vals = self._compute_account_op_balance(wizard, account_ids)
            for key in bal_vals:
                if key not in op_bal_vals:
                    op_bal_vals[key] = {'account_id': item, 'op_debit': 0, 'op_credit': 0, 'op_balance': 0}
                if key in op_bal_vals:
                    bal_vals[key].update(op_bal_vals[key])
                    bal_vals[key]['fn_balance'] = bal_vals[key].get('balance', 0) + bal_vals[key].get('op_balance', 0)
                    bal_vals[key]['fn_debit'] = bal_vals[key].get('debit', 0) + bal_vals[key].get('op_debit', 0)
                    bal_vals[key]['fn_credit'] = bal_vals[key].get('credit', 0) + bal_vals[key].get('op_credit', 0)
        for key in bal_vals:
            account_rec = self.env['account.account'].browse([key])
            bal_vals[key]['account_name'] = account_rec.display_name if account_rec else str(key)
        return bal_vals

    def update_partners_bal_values(self, wizard, op_bal, partner_ids):
        bal_vals = self._compute_partner_balance(wizard, partner_ids)

        val_ids = [id for id in bal_vals]
        for item in partner_ids.ids:
            if item not in val_ids:
                bal_vals[item] = {'partner_id': item, 'debit': 0, 'credit': 0, 'balance': 0}

        if op_bal == True:
            op_bal_vals = self._compute_partner_op_balance(wizard, partner_ids)
            for key in bal_vals:
                if key not in op_bal_vals:
                    op_bal_vals[key] = {'partner_id': item, 'op_debit': 0, 'op_credit': 0, 'op_balance': 0}
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
                account_ids = self.env['account.account'].search([], order='code asc')
            val_lines = self.update_accounts_bal_values(wizard, wizard.opening_balance, account_ids)
        if wizard.group_by == 'partner':
            partner_ids = wizard.partner_ids
            if not partner_ids:
                partner_domain = []
                if wizard.partner_type in ['receivable']:
                    partner_domain.append(('customer_rank', '>', 0))
                if wizard.partner_type in ['payable']:
                    partner_domain.append(('supplier_rank', '>', 0))
                partner_ids = self.env['res.partner'].search(partner_domain)
            val_lines = self.update_partners_bal_values(wizard, wizard.opening_balance, partner_ids)

        if wizard.without_zero:
            lines = [item for item in val_lines.values() if 'balance' in item and item['balance'] != 0]
        else:
            lines = [item for item in val_lines.values()]
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
