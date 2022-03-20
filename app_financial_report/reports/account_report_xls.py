from odoo import models, fields, api, _
from datetime import datetime
import os



class ReportAccountLedgerXls(models.AbstractModel):
    _name = 'report.app_financial_report.report_ledger_xlsx_template'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, wizard):

        sheet = workbook.add_worksheet("Accounting Ledger")

        header_format_sheet = workbook.add_format({'font_size': 10,
                                            'font_color': 'white',
                                            'align': 'center',
                                            'right': True,
                                            'left': True,
                                            'bottom': True,
                                            'top': True,
                                            'bold': True})
        header_format_sheet.set_bg_color('#395870')  # pylint: disable=redefined-builtin

        section_format_sheet = workbook.add_format({'font_size': 10,
                                             'bottom': True,
                                             'right': True,
                                             'left': True,
                                             'top': True,
                                             'bold': True})
        section_format_sheet.set_align('center')
        section_format_sheet.set_align('vcenter')


        data_font_size_8 = workbook.add_format({'bottom': True, 'top': True, 'right': True, 'left': True, 'font_size': 10,'num_format': '#,##0.00_);(#,##0.00)'})

        data_font_size_8.set_align('center')


        data_font_size_88 = workbook.add_format({'font_color': 'white','bold': True,'bottom': True, 'top': True, 'right': True, 'left': True, 'font_size': 10})

        data_font_size_88.set_align('center')
        data_font_size_88.set_bg_color('#395870')


        data_font_size_85 = workbook.add_format({'font_color': 'blue','bold': True,'bottom': True, 'top': True, 'right': True, 'left': True, 'font_size': 10})

        data_font_size_85.set_align('center')

        prod_row = 0
        sheet.merge_range('A' + str(prod_row + 1) + ':E' + str(prod_row + 2), "Accounting Ledger", section_format_sheet)
        prod_row = prod_row + 2
        prod_col = 0
        col_name = 0
        col_debit = 1
        col_credit = 2
        col_bal = 3
        header_report = ['Name', 'Debit', 'Credit', 'Balance']
        if not wizard.debit_credit:
            col_bal = 1
        if wizard.opening_balance == True:
            if wizard.debit_credit == True:
                op_col_debit = 1
                op_col_credit = 2
                op_col_bal = 3
                col_debit = 4
                col_credit = 5
                col_bal = 6
                fn_col_debit = 7
                fn_col_credit = 8
                fn_col_bal = 9
            else:
                op_col_bal = 1
                col_bal = 2
                fn_col_bal = 3
            header_report = ['Name', 'O-Debit', 'O-Credit', 'O-Balance', 'Debit', 'Credit', 'Balance', 'F-Debit', 'F-Credit', 'F-Balance']
        for header_val in header_report:
            sheet.write(prod_row, prod_col, header_val, header_format_sheet)
            sheet.set_column(prod_row, prod_col, len(header_val) * 5)
            prod_col += 1
        for line in self.get_account_lines(wizard):
            prod_row += 1
            sheet.write(prod_row, col_name, line.get('name', False), data_font_size_88)
            sheet.set_column(prod_row, col_name, len(line.get('name', False)) * 1.5)
            sheet.write(prod_row, col_bal, line.get('balance', False), data_font_size_85)
            if wizard.debit_credit:
                sheet.write(prod_row, col_debit, line.get('debit', False), data_font_size_8)
                sheet.write(prod_row, col_credit, line.get('credit', False), data_font_size_8)

            if wizard.opening_balance:
                sheet.write(prod_row, op_col_bal, line.get('op_balance', False), data_font_size_85)
                if wizard.debit_credit:
                    sheet.write(prod_row, op_col_debit, line.get('op_debit', False), data_font_size_8)
                    sheet.write(prod_row, op_col_credit, line.get('op_credit', False), data_font_size_8)
                ###
                sheet.write(prod_row, fn_col_bal, line.get('fn_balance', False), data_font_size_85)
                if wizard.debit_credit:
                    sheet.write(prod_row, fn_col_debit, line.get('fn_debit', False), data_font_size_8)
                    sheet.write(prod_row, fn_col_credit, line.get('fn_credit', False), data_font_size_8)

    def date_str(self, date):
        return datetime.strftime(date, '%Y-%m-%d')

    def where_sql(self, wizard, op_balance):
        whare_str = " AND m.state != 'cancel'"
        if op_balance:
            if wizard.date_from:
                whare_str = " AND m_line.date < '" + self.date_str(wizard.date_from) + "' "
        else:
            if wizard.date_from:
                whare_str += " AND m_line.date >= '" + self.date_str(wizard.date_from) + "' "
            if wizard.date_to:
                whare_str += " AND m_line.date <= '" + self.date_str(wizard.date_to) + "' "

        if wizard.target_move == 'posted':
            whare_str += " AND m.state in ('posted') "
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
                SUM(m_line.debit) as op_debit,
                SUM(m_line.credit) as op_credit,
                (SUM(m_line.debit)-SUM(m_line.credit)) as op_balance
                FROM account_move_line m_line
                JOIN account_move m ON
                m_line.move_id = m.id
                """
        if query_where:
            query_all = query_all + query_where + " group by m_line.account_id order by m_line.account_id "
        else:
            query_all = query_all + " group by m_line.account_id order by m_line.account_id "

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
            query_all = query_all + query_where + " group by m_line.account_id order by m_line.account_id "
        else:
            query_all = query_all + " group by m_line.account_id order by m_line.account_id "

        self.env.cr.execute(query_all)

        result = self.env.cr.dictfetchall()
        result2 = {}
        for row in result:
            result2[row['account_id']] = row
        if not result:
            for key in account_ids:
                result2[key] = {'account_id': key, 'debit': 0, 'credit': 0, 'balance': 0}
        return result2

    def _compute_partner_op_balance(self, wizard, partners):
        query_where = "where m_line.move_id = m.id "
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
                JOIN account_move m ON
                m_line.move_id = m.id
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
        query_where = "where m_line.move_id = m.id "
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
                JOIN account_move m ON
                m_line.move_id = m.id
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
                result2[key] = {'partner_id': key, 'debit': 0, 'credit': 0, 'balance': 0}
        return result2

    def update_accounts_bal_values(self, wizard, op_bal, account_ids):
        bal_vals = self._compute_account_balance(wizard, account_ids)

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
            bal_vals[key]['name'] = account_rec.display_name if account_rec else str(key)
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
            bal_vals[key]['name'] = partner_rec.display_name if partner_rec else str(key)
        return bal_vals

    def get_account_lines(self, wizard):
        lines = []
        val_lines = {}
        if wizard.group_by == 'account':
            account_ids = wizard.account_ids
            if not account_ids:
                account_ids = self.env['account.account'].search([])
            val_lines = self.update_accounts_bal_values(wizard, wizard.opening_balance, account_ids)
        if wizard.group_by == 'partner':
            partner_ids = wizard.partner_ids
            if not partner_ids:
                partner_ids = self.env['res.partner'].search([])
            val_lines = self.update_partners_bal_values(wizard, wizard.opening_balance, partner_ids)
        lines = [item for item in val_lines.values()]
        return lines
