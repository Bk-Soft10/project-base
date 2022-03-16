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

        #lines = self.getFilterdValue(wizard)

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
            sheet.write(prod_row, col_account, "", data_font_size_88)
            ddd_data = self.get_account_report(wizard, root_tree)
            if root_tree.type == 'sum':
                sheet.write(prod_row, col_bal, self.get_sum_report_balance(wizard, root_tree), data_font_size_88)
            elif root_tree.type == 'account_report' and root_tree.account_report_id:
                sheet.write(prod_row, col_bal, self.get_sum_report_balance(wizard, root_tree.account_report_id), data_font_size_88)
            else:
                sum_balance = sum(float(pp['balance_sum']) for pp in ddd_data)
                sheet.write(prod_row, col_bal, sum_balance, data_font_size_8)
            bal_sum = 0
            if root_tree.type in ['accounts', 'account_type']:
                for parent_root in ddd_data:
                    prod_row = prod_row + 1
                    account_id = self.env['account.account'].search([('id', '=', int(parent_root['account_id']))], limit=1)
                    sheet.write(prod_row, col_account, account_id.display_name, data_font_size_8)
                    sheet.write(prod_row, col_bal, parent_root['balance_sum'], data_font_size_8)
                    bal_sum = bal_sum + float(parent_root['balance_sum'])

    def get_sum_report_balance(self, wizard, report):
        if report.type == 'sum':
            bl = 0.00
            for report_child_id in report._get_children_by_order():
                if report_child_id.type == 'account_report' and report_child_id.account_report_id:
                    for report_child_idd in report_child_id.account_report_id._get_children_by_order():
                        bl += sum(float(acc_data['balance_sum']) for acc_data in self.get_account_report(wizard, report_child_idd))
                bl += sum(float(acc_data['balance_sum']) for acc_data in self.get_account_report(wizard, report_child_id))
            return bl
        if report.type == 'account_report':
            bl = 0.00
            for report_child_id in report.account_report_id._get_children_by_order():
                bl += sum(float(acc_data['balance_sum']) for acc_data in self.get_account_report(wizard, report_child_id))
            return bl

    def get_account_report(self, wizard, report):
        accounts = False
        account_lines = []
        if report.type == 'accounts':
            accounts = self.env['account.account'].search([('id', 'in', report.account_ids.ids)])
        elif report.type == 'account_type':
            accounts = self.env['account.account'].search([('user_type_id.id', 'in', report.account_type_ids.ids)])

        # elif report.type == 'sum':
        #     accounts = False
        #     accounts = report._get_children_by_order().filtered(lambda ex: ex.type == 'accounts').mapped('account_ids')
        #     sum_report_account_type = report._get_children_by_order().filtered(lambda ex: ex.type == 'account_type').mapped('account_type_ids')
        #     accounts += self.env['account.account'].search([('user_type_id.id', 'in', sum_report_account_type.ids if sum_report_account_type else [])])
        else:
            accounts = False
        if accounts:
            account_lines = self._get_bal_accounts(wizard, report, accounts.ids)
        return account_lines

    def _get_bal_accounts(self, wizard, report, account_ids):
        account_lines = []
        data_account_line = self.getFilterdValue(wizard, account_ids)
        if data_account_line:
            for line in data_account_line:
                account_lines.append(({
                    'account_id': line[0],
                    'account_name': line[1],
                    'account_code': line[2],
                    'debit_sum': line[3],
                    'credit_sum': line[4],
                    'balance_sum': line[5],
                    'group_type': report.type,
                    'group_id': report.id,
                }))
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
        SELECT m_line.account_id as account,
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

        result = self.env.cr.fetchall() or False
        return result
