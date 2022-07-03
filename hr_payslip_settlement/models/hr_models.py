# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
# from datetime import datetime
from datetime import timedelta, date, datetime
from dateutil.relativedelta import relativedelta
from odoo.osv import expression
from odoo.exceptions import UserError, ValidationError

##########################################################################################################################################
#########################################################################################################################################

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    settlement_line_ids = fields.One2many('hr.payslip.settlement.lines', 'employee_id', string='settlement Lines')
    settlement_ids = fields.One2many('hr.payslip.settlement', 'employee_id', string='settlements')

    def compute_settlement(self, r_code, payslip):
        # self.settlement_ids.update_lines_month()
        clause_final = [('settlement_id.employee_id', '=', self.id), ('settlement_id.state', '=', 'approved'), ('settlement_id.settlement_type.code', '=', r_code)]

        list_ids = self.env['hr.payslip.settlement.lines'].search(clause_final)
        uplist_ids = list_ids.filtered(lambda st: st.date_start >= payslip.date_from and st.date_start <= payslip.date_to and st.date_end >= payslip.date_from and st.date_end <= payslip.date_to)
        result = 0
        for rec in uplist_ids:
            if rec.settlement_id.request_type == 'deduct':
                result += rec.settlement_id.month_amount * -1
            if rec.settlement_id.request_type == 'allowance':
                result += rec.settlement_id.month_amount
        return result

##########################################################################################################################################
#########################################################################################################################################

class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    def action_payslip_done(self):
        res = super(HrPayslip, self).action_payslip_done()
        for rec in self:
            if rec.employee_id and rec.employee_id.settlement_ids:
                rec.employee_id.settlement_ids._compute_paid_lines()