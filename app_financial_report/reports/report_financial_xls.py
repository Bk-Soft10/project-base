from odoo import models, fields, api, _
from datetime import datetime
import os

HEADER_VALS1 = ['Group',
                'Account',
                'Balance']
HEADER_VALS2 = ['Group', 'Account', 'Opening Balance', 'Balance', 'Final Balance']


class ReportFinancialXls(models.AbstractModel):
    _name = 'report.app_financial_report.report_financial_xlsx_template'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, wizard):

        sheet = workbook.add_worksheet(wizard.account_report_id.name)

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
        sheet.merge_range('A' + str(prod_row + 1) + ':E' + str(prod_row + 2), wizard.account_report_id.name, section_format_sheet)
        prod_row = prod_row + 2
        prod_col = 0
        col_group = 0
        col_account = 1
        col_bal = 2
        col_op_bal = 3
        col_fn_bal = 4
        header_report = HEADER_VALS1
        if wizard.opening_balance == True:
            col_bal = 3
            col_op_bal = 2
            col_fn_bal = 4
            header_report = HEADER_VALS2
        for header_val in header_report:
            sheet.write(prod_row, prod_col, header_val, header_format_sheet)
            sheet.set_column(prod_row, prod_col, len(header_val) * 5)
            prod_col += 1
        for root_tree in wizard.account_report_id._get_children_by_order():
            prod_row += 1
            if root_tree.type == 'sum':
                sheet.write(prod_row, col_group, root_tree.name, data_font_size_88)
            elif root_tree.type == 'account_report':
                sheet.write(prod_row, col_group, root_tree.name, data_font_size_88)
            else:
                sheet.write(prod_row, col_group, root_tree.name, data_font_size_8)
                # pass
            sheet.set_column(prod_row, col_group, len(root_tree.name) * 5)
            if root_tree.type == 'sum':
                sheet.write(prod_row, col_account, "", data_font_size_88)
            if root_tree.type == 'account_report':
                sheet.write(prod_row, col_account, "", data_font_size_88)
            if root_tree.type == 'account_type':
                sheet.write(prod_row, col_account, "", data_font_size_8)
            if root_tree.type == 'accounts':
                sheet.write(prod_row, col_account, "", data_font_size_8)
            ddd_data = self.get_account_report(wizard, root_tree)
            if root_tree.type == 'sum':
                sheet.write(prod_row, col_bal, self.get_sum_report_balance(wizard, root_tree), data_font_size_88)
                if wizard.opening_balance == True:
                    sheet.write(prod_row, col_op_bal, self.get_sum_report_op_balance(wizard, root_tree), data_font_size_88)
                    sheet.write(prod_row, col_fn_bal, self.get_sum_report_fn_balance(wizard, root_tree), data_font_size_88)
            elif root_tree.type == 'account_report' and root_tree.account_report_id:
                sheet.write(prod_row, col_bal, self.get_sum_report_balance(wizard, root_tree.account_report_id), data_font_size_88)
                if wizard.opening_balance == True:
                    sheet.write(prod_row, col_op_bal, self.get_sum_report_op_balance(wizard, root_tree.account_report_id), data_font_size_88)
                    sheet.write(prod_row, col_fn_bal, self.get_sum_report_fn_balance(wizard, root_tree.account_report_id), data_font_size_88)
            else:
                sum_balance = sum(float(pp['balance_sum']) for pp in ddd_data)
                sheet.write(prod_row, col_bal, sum_balance, data_font_size_8)
                if wizard.opening_balance == True:
                    sum_op_balance = sum(float(pp['op_balance_sum']) for pp in ddd_data)
                    sum_fn_balance = sum(float(pp['fn_balance_sum']) for pp in ddd_data)
                    sheet.write(prod_row, col_op_bal, sum_op_balance, data_font_size_8)
                    sheet.write(prod_row, col_fn_bal, sum_fn_balance, data_font_size_8)
            # bal_sum = 0
            if root_tree.type in ['accounts', 'account_type']:
                for parent_root in ddd_data:
                    prod_row = prod_row + 1
                    account_id = self.env['account.account'].search([('id', '=', int(parent_root['account_id']))], limit=1)
                    sheet.write(prod_row, col_account, account_id.display_name, data_font_size_8)
                    sheet.write(prod_row, col_bal, parent_root['balance_sum'] if 'balance_sum' in parent_root else 0, data_font_size_8)
                    if wizard.opening_balance == True:
                        sheet.write(prod_row, col_op_bal, parent_root['op_balance_sum'] if 'op_balance_sum' in parent_root else 0, data_font_size_8)
                        sheet.write(prod_row, col_fn_bal, parent_root['fn_balance_sum'] if 'fn_balance_sum' in parent_root else 0, data_font_size_8)
                    # bal_sum = bal_sum + float(parent_root['balance_sum'])

    def get_sum_report_balance(self, wizard, report):
        if report.type == 'sum':
            bl = 0.00
            for report_child_id in report._get_children_by_order():
                if report_child_id.type == 'account_report' and report_child_id.account_report_id:
                    for report_child_idd in report_child_id.account_report_id._get_children_by_order():
                        bl += sum(round(acc_data['balance_sum'], 2) for acc_data in self.get_account_report(wizard, report_child_idd))
                bl += sum(round(acc_data['balance_sum'], 2) for acc_data in self.get_account_report(wizard, report_child_id))
            return round(bl, 2)
        if report.type == 'account_report':
            bl = 0.00
            for report_child_id in report.account_report_id._get_children_by_order():
                bl += sum(round(acc_data['balance_sum'], 2) for acc_data in self.get_account_report(wizard, report_child_id))
            return round(bl, 2)

    def get_sum_report_op_balance(self, wizard, report):
        if report.type == 'sum':
            bl = 0.00
            for report_child_id in report._get_children_by_order():
                if report_child_id.type == 'account_report' and report_child_id.account_report_id:
                    for report_child_idd in report_child_id.account_report_id._get_children_by_order():
                        bl += sum(round(acc_data['op_balance_sum'], 2) for acc_data in self.get_account_report(wizard, report_child_idd))
                bl += sum(round(acc_data['op_balance_sum'], 2) for acc_data in self.get_account_report(wizard, report_child_id))
            return round(bl, 2)
        if report.type == 'account_report':
            bl = 0.00
            for report_child_id in report.account_report_id._get_children_by_order():
                bl += sum(round(acc_data['op_balance_sum'], 2) for acc_data in self.get_account_report(wizard, report_child_id))
            return round(bl, 2)

    def get_sum_report_fn_balance(self, wizard, report):
        if report.type == 'sum':
            bl = 0.00
            for report_child_id in report._get_children_by_order():
                if report_child_id.type == 'account_report' and report_child_id.account_report_id:
                    for report_child_idd in report_child_id.account_report_id._get_children_by_order():
                        bl += sum(round(acc_data['fn_balance_sum'], 2) for acc_data in self.get_account_report(wizard, report_child_idd))
                bl += sum(round(acc_data['fn_balance_sum'], 2) for acc_data in self.get_account_report(wizard, report_child_id))
            return round(bl, 2)
        if report.type == 'account_report':
            bl = 0.00
            for report_child_id in report.account_report_id._get_children_by_order():
                bl += sum(round(acc_data['fn_balance_sum'], 2) for acc_data in self.get_account_report(wizard, report_child_id))
            return round(bl, 2)

    def get_account_report(self, wizard, report):
        accounts = False
        account_lines = []
        if report.type == 'accounts':
            accounts = self.env['account.account'].search([('id', 'in', report.account_ids.ids)])
        elif report.type == 'account_type':
            accounts = self.env['account.account'].search([('user_type_id.id', 'in', report.account_type_ids.ids)])
        else:
            accounts = False
        if accounts:
            account_lines = self._get_bal_accounts(wizard, report, accounts.ids)
        return account_lines

    def _get_bal_accounts(self, wizard, report, account_ids):
        account_lines = []
        # data_account_line, dict_bal = self.getFilterdValue(wizard, account_ids.ids)
        data_account_line, dict_bal = self._compute_account_balance(account_ids)
        if wizard.opening_balance == True:
            # data_account_op, dict_op_bal = self.getOPFilterdValue(wizard, account_ids.ids)
            data_account_op, dict_op_bal = self._compute_account_op_balance(account_ids)
            for key in dict_bal:
                if key in dict_op_bal:
                    # if key not in dict_bal:
                    #     dict_bal[key.id] = {'account_id': key.id, 'account_name': key.name, 'account_code': key.code, 'debit_sum': 0, 'credit_sum': 0, 'balance_sum': 0}
                    account_rec = self.env['account.account'].browse([key])
                    if account_rec:
                        dict_bal[key].update({'account_id': account_rec.id, 'account_name': account_rec.name, 'account_code': account_rec.code})
                    dict_bal[key].update(dict_op_bal[key])
                # if key not in dict_op_bal:
                #     dict_bal[key.id] = {'op_debit_sum': 0, 'op_credit_sum': 0, 'op_balance_sum': 0}
            data_account_line = [item for item in dict_bal.values()]
            print(data_account_line)
        if data_account_line:
            for line in data_account_line:
                line_dict = {
                    'account_id': line.get('account_id'),
                    'account_name': line.get('account_name'),
                    'account_code': line.get('account_code'),
                    'debit_sum': round(line.get('debit_sum'), 2) if 'debit_sum' in line else 0,
                    'credit_sum': round(line.get('credit_sum'), 2) if 'credit_sum' in line else 0,
                    'balance_sum': round(line.get('balance_sum'), 2) if 'balance_sum' in line else 0,
                    'group_type': report.type,
                    'group_id': report.id,
                }
                if wizard.opening_balance == True:
                    line_dict['op_debit_sum'] = round(line.get('op_debit_sum'), 2) if 'op_debit_sum' in line else 0
                    line_dict['op_credit_sum'] = round(line.get('op_credit_sum'), 2) if 'op_credit_sum' in line else 0
                    line_dict['op_balance_sum'] = round(line.get('op_balance_sum'), 2) if 'op_balance_sum' in line else 0
                    line_dict['fn_debit_sum'] = line_dict.get('op_debit_sum') + line_dict.get('debit_sum')
                    line_dict['fn_credit_sum'] = line_dict.get('op_credit_sum') + line_dict.get('credit_sum')
                    line_dict['fn_balance_sum'] = line_dict.get('op_balance_sum') + line_dict.get('balance_sum')
                account_lines.append(line_dict)
        return account_lines

    def getFilterdValue(self, wizard, account_ids):
        query_where = "where m_line.move_id = m.id "

        if wizard.target_move == 'posted':
            query_where += " and m.state = 'posted' "

        if account_ids:
            if (len(account_ids) == 1):
                query_where += " and m_line.account_id = %s " % (account_ids[0])
            else:
                query_where += " and m_line.account_id IN %s " % (tuple(account_ids),)

        if wizard.date_from or wizard.date_to:
            if wizard.date_from:
                query_where += " and m_line.date >= '%s'" % (datetime.strptime(str(wizard.date_from), '%Y-%m-%d'),)
            if wizard.date_to:
                query_where += " and m_line.date <= '%s'" % (datetime.strptime(str(wizard.date_to), '%Y-%m-%d'),)

        query_all = """
        SELECT m_line.account_id as account_id,
        acc.name as account_name,
        acc.code as account_code,
        SUM(m_line.debit) as debit_sum,
        SUM(m_line.credit) as credit_sum,
        (SUM(m_line.debit)-SUM(m_line.credit)) as balance_sum
        FROM account_move_line m_line
        JOIN account_move m ON
        m_line.move_id = m.id
        JOIN account_account acc ON
        m_line.account_id = acc.id
        """
        if query_where:
            query_all = query_all + query_where + " group by m_line.account_id,acc.name,acc.id "
        else:
            query_all = query_all + " group by m_line.account_id "

        self.env.cr.execute(query_all)

        result = self.env.cr.dictfetchall() or False
        result2 = {}
        for row in result:
            result2[row['account_id']] = row
        return result, result2

    def getOPFilterdValue(self, wizard, account_ids):
        query_where = "where m_line.move_id = m.id "

        if wizard.target_move == 'posted':
            query_where += " and m.state = 'posted' "

        if account_ids:
            if (len(account_ids) == 1):
                query_where += " and m_line.account_id = %s " % (account_ids[0])
            else:
                query_where += " and m_line.account_id IN %s " % (tuple(account_ids),)

        if wizard.date_from:
            query_where += " and m.date < '%s'" % (datetime.strptime(str(wizard.date_from), '%Y-%m-%d'),)

        query_all = """
        SELECT m_line.account_id as account_id,
        acc.name as account_name,
        acc.code as account_code,
        SUM(m_line.debit) as op_debit_sum,
        SUM(m_line.credit) as op_credit_sum,
        (SUM(m_line.debit)-SUM(m_line.credit)) as op_balance_sum
        FROM account_move_line m_line
        JOIN account_move m ON
        m_line.move_id = m.id
        JOIN account_account acc ON
        m_line.account_id = acc.id
        """
        if query_where:
            query_all = query_all + query_where + " group by m_line.account_id,acc.name,acc.id "
        else:
            query_all = query_all + " group by m_line.account_id "

        self.env.cr.execute(query_all)

        result = self.env.cr.dictfetchall() or False
        result2 = {}
        for row in result:
            result2[row['account_id']] = row
        return result, result2

    def _compute_account_balance(self, accounts):
        mapping = {
            'balance_sum': "COALESCE(SUM(debit),0) - COALESCE(SUM(credit), 0) as balance_sum",
            'debit_sum': "COALESCE(SUM(debit), 0) as debit_sum",
            'credit_sum': "COALESCE(SUM(credit), 0) as credit_sum",
        }

        res = {}
        for account in accounts:
            res[account] = dict.fromkeys(mapping, 0.0)
        if accounts:
            tables, where_clause, where_params = self.env['account.move.line']._query_get()
            tables = tables.replace('"', '') if tables else "account_move_line"
            wheres = [""]
            if where_clause.strip():
                wheres.append(where_clause.strip())
            filters = " AND ".join(wheres)
            request = "SELECT account_id as account_id, " + ', '.join(mapping.values()) + \
                      " FROM " + tables + \
                      " WHERE account_id IN %s " \
                      + filters + \
                      " GROUP BY account_id"
            params = (tuple(accounts),) + tuple(where_params)
            self.env.cr.execute(request, params)
            result = self.env.cr.dictfetchall()
            for row in result:
                res[row['account_id']] = row
        return result, res

    def _compute_account_op_balance(self, accounts):
        mapping = {
            'op_balance_sum': "COALESCE(SUM(debit),0) - COALESCE(SUM(credit), 0) as op_balance_sum",
            'op_debit_sum': "COALESCE(SUM(debit), 0) as op_debit_sum",
            'op_credit_sum': "COALESCE(SUM(credit), 0) as op_credit_sum",
        }

        res = {}
        for account in accounts:
            res[account] = dict.fromkeys(mapping, 0.0)
        if accounts:
            tables, where_clause, where_params = self.env['account.move.line'].with_context(initial_bal=True, date_to=False)._query_get()
            tables = tables.replace('"', '') if tables else "account_move_line"
            wheres = [""]
            if where_clause.strip():
                wheres.append(where_clause.strip())
            filters = " AND ".join(wheres)
            request = "SELECT account_id as account_id, " + ', '.join(mapping.values()) + \
                      " FROM " + tables + \
                      " WHERE account_id IN %s " \
                      + filters + \
                      " GROUP BY account_id"
            params = (tuple(accounts),) + tuple(where_params)
            self.env.cr.execute(request, params)
            result = self.env.cr.dictfetchall()
            for row in result:
                res[row['account_id']] = row
        return result, res
