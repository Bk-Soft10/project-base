# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
# from datetime import datetime
from datetime import timedelta, date, datetime
from dateutil.relativedelta import relativedelta
from odoo.osv import expression
from odoo.exceptions import UserError, ValidationError


##########################################################################################################################################
#########################################################################################################################################

class SettlementType(models.Model):
    _name = 'payslip.settlement.type'
    _description = 'Settlement Type'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name', required=True)
    type = fields.Selection([('deduct', 'Deduction'), ('allowance', 'Allowance')], defaut='deduct', string='Type', required=True)
    rule_id = fields.Many2one('hr.salary.rule', string='Salary Rule')
    code = fields.Char(related='rule_id.code', string='Code', store=True)
    state = fields.Selection([('draft', 'Draft'), ('confirmed', 'Confirmed')], default='draft')
    portal_service = fields.Boolean(string='Requested From Portal?')
    amount = fields.Float('Amount')

    def action_confirm(self):
        for rec in self:
            if rec.state == 'draft':
                rec.state = 'confirmed'
                salary_rule = self.env['hr.salary.rule'].sudo()
                rule_name = rec.name
                rule_code = "DSET_%d" % rec.id
                categ_id = self.env.ref('hr_payroll_community.DED').id
                if type == 'allowance':
                    rule_code = "ASET_%d" % rec.id
                    categ_id = self.env.ref('hr_payroll_community.ALW').id
                rule_dict = {
                    'name': rule_name,
                    'category_id': categ_id,
                    'code': rule_code,
                    'sequence': 20,
                    'condition_select': 'python',
                    'condition_python': "result = employee.compute_settlement('%s', payslip)" % rule_code,
                    'amount_select': 'code',
                    'amount_python_compute': "result =employee.compute_settlement('%s', payslip)" % rule_code,
                }
                rule_id = salary_rule.create(rule_dict)
                rec.code = rule_code
                rec.rule_id = rule_id.id
                struct = self.env.ref('hr_payroll_community.structure_base').sudo()
                struct.rule_ids = [(4, rule_id.id)]

##########################################################################################################################################
#########################################################################################################################################

class HrPayslipSettlement(models.Model):
    _name = 'hr.payslip.settlement'
    _rec_name = 'employee_id'
    _description = 'Employee Payslip settlement'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, index=True)
    emp_no = fields.Char(string='Employee No', index=True)
    department_id = fields.Many2one('hr.department', string='Department')
    job_id = fields.Many2one('hr.job', string='Job Title')
    request_date = fields.Date(string='Request Date', required=True, default=datetime.today())
    date_start = fields.Date(string='Start Date', required=True)
    duration = fields.Integer(string='Duration', required=True)
    date_end = fields.Date(string='End Date', compute='_compute_date_end_discount', store=True)
    calculation_method = fields.Selection([('amount', _('Fixed Amount')), ('percentage', _('Percentage')), ('percentage_of_day', _('Percentage Of Working Day')),('days',_('Working Days')),('hour',_('Working Hours'))], string='Calculation Method')
    calculation_based = fields.Selection([('basic_salary', _('Basic Salary')), ('gross_salary', _('Gross Salary'))], string='Calculation Based', default='gross_salary')
    amount = fields.Float(string='Amount/Percentage Of Day/Working Days #/Working Hours #', digits='Payroll')
    month_amount = fields.Float(string='Final Amount', compute='_compute_final_amount', digits='Payroll')
    total_amount = fields.Float(string='Total amount', compute='_compute_final_amount', store=True, digits='Payroll')
    amount_deducted = fields.Float(string='Amount Paid', readonly=True, digits='Payroll', store=True, compute= '_compute_paid_lines')
    remain_amount = fields.Float(string='Remaining amount', compute='_compute_final_amount', digits='Payroll')
    reason = fields.Html(string='Reason Settlement')
    settlement_line_ids = fields.One2many('hr.payslip.settlement.lines', 'settlement_id', string='Lines')
    request_type = fields.Selection([('deduct', 'Deduction'), ('allowance', 'Allowance')], default='deduct', required=True)
    settlement_type = fields.Many2one('payslip.settlement.type', string='Settlement Type', required=True)
    attachment_ids = fields.Many2many('ir.attachment', string='Attachments')
    portal_service = fields.Boolean(string='Requested From Portal?')
    state = fields.Selection([('draft', 'HRO'), ('waitting_approve', 'HRM'),
                              ('approved', 'Approved'), ('cancel', 'Cancelled'), ('close', 'Closed')], default='draft')
    # sql_constraints = [
    #     ('emp_no_uniq', 'unique(emp_no)', _("The Employee Number must be unique"))
    # ]

    def send_email(self):
        for rec in self:
            group_user = self.env.ref('hr_payslip_settlement.group_hr_settlement_user').users
            group_user and self.message_post(body=_(
                'Please Set Your Approval on settlement request for %s' % rec.sudo().employee_id.name),
                email_from=self.env.user.company_id.email,
                partner_ids=[user.partner_id.id for user in group_user])

    def _compute_paid_lines(self):
        for rec in self:
            rec.amount_deducted = 0
            if rec.settlement_line_ids:
                rec.settlement_line_ids._get_settlement_line_paid()
                rec.amount_deducted = sum(ll.settlement_id.month_amount for ll in rec.settlement_line_ids if ll.paid == True) or 0

    @api.depends('amount', 'calculation_method', 'calculation_based', 'employee_id', 'amount_deducted', 'duration')
    def _compute_final_amount(self):
        amount = 0.0
        for rec in self:
            if rec.calculation_method == 'amount' and rec.amount:
                amount = rec.amount
            elif rec.calculation_method == 'percentage' and rec.employee_id.contract_id:
                if rec.calculation_based == 'basic_salary':
                    amount = (rec.amount / 100) * (rec.employee_id.contract_id.wage)
                # else:
                #     amount = (rec.amount / 100)*(rec.employee_id.contract_id.total_gross_salary)
            elif rec.calculation_method == 'percentage_of_day' and rec.employee_id.contract_id:
                if rec.calculation_based =='basic_salary':
                    amount = (rec.amount / 100)*(rec.employee_id.contract_id.wage/30)
                # else:
                #     amount = (rec.amount / 100)*(rec.employee_id.contract_id.total_gross_salary/30)
            elif rec.calculation_method == 'days' and rec.employee_id.contract_id:
                if rec.calculation_based == 'basic_salary':
                    amount = rec.amount * (rec.employee_id.contract_id.wage/30)
                # else:
                #     amount = rec.amount * (rec.employee_id.contract_id.total_gross_salary/30)
            elif rec.calculation_method == 'hour' and rec.employee_id.contract_id:
                if rec.calculation_based == 'basic_salary':
                    amount = rec.amount * (rec.employee_id.contract_id.wage/30/8)
                # else:
                #     amount = rec.amount * (rec.employee_id.contract_id.total_gross_salary/30/8)
            rec.month_amount = amount
            rec.total_amount = rec.duration * amount
            rec.total_amount = rec.duration * amount
            remain_amount = (rec.duration * amount) - rec.amount_deducted
            rec.remain_amount = remain_amount
            # if not remain_amount:
            #     rec.write({'state':'close'})

    @api.depends('date_start', 'duration')
    def _compute_date_end_discount(self):
        for rec in self:
            if rec.date_start and rec.duration:
                compute_discount = rec.date_start + relativedelta(months=rec.duration) + relativedelta(days=-1)
                rec.date_end = compute_discount
                rec.update_lines_month()

    def update_all_record(self):
        for rec in self.search([]):
            rec.update_lines_month()

    def update_lines_month(self):
        for rec in self:
            if rec.employee_id and rec.date_start and rec.duration and rec.month_amount:
                rec.settlement_line_ids.unlink()
                line_lst = []
                start_month = date(rec.date_start.year, rec.date_start.month, 1)
                for ii in range(int(rec.duration)):
                    end_month = start_month + relativedelta(months=1) + relativedelta(days=-1)
                    line_lst.append((0, 0, {
                        'date_start': start_month,
                        'date_end': end_month,
                    }))
                    # mm = ii + 1
                    # print(mm)
                    start_month = start_month + relativedelta(months=1)
                if line_lst and len(line_lst) > 0:
                    rec.settlement_line_ids = line_lst
                rec._compute_paid_lines()

    def name_get(self):
        ret = []
        for rec in self:
            ret.append((rec.id, _('Employee Settlement - ') + rec.employee_id.name))
        return ret

    @api.onchange('request_type')
    def onchange_request_type(self):
        self.settlment_type = False
        return {'domain': {'settlement_type': [('type', '=', self.request_type), ('state', '=', 'confirmed')]}}

    @api.onchange('employee_id')
    def _onchange_employee(self):
        for rec in self:
            if rec.employee_id:
                rec.department_id = rec.employee_id.department_id.id
                # rec.emp_no = rec.employee_id.employee_no
                rec.job_id = rec.employee_id.job_id.id

    def action_draft(self):
        for rec in self:
            rec.state = 'draft'

    def action_waitting_approval(self):
        for rec in self:
            rec.state = 'waitting_approve'

    def action_approved(self):
        for rec in self:
            rec.state = 'approved'
            rec.update_lines_month()

    def action_cancel(self):
        for rec in self:
            rec.state = 'cancel'

    def action_close(self):
        for rec in self:
            rec.state = 'close'

    @api.constrains('date_start')
    def _check_date_start(self):
        for record in self:
            if record.date_start < record.request_date:
                raise ValidationError(_('The start date of the settlement cannot be less than request date'))

    def unlink(self):
        if any(self.filtered(lambda record: record.state in ['approved', 'cancel', 'close'])):
            raise UserError(_('You cannot delete a record after approved or cancel!'))
        return super(HrPayslipSettlement, self).unlink()

##########################################################################################################################################
#########################################################################################################################################

class HrPayslipSettlementLine(models.Model):
    _name = 'hr.payslip.settlement.lines'

    settlement_id = fields.Many2one('hr.payslip.settlement', string='settlement')
    employee_id = fields.Many2one('hr.employee', string='Employee', store=True, related='settlement_id.employee_id')
    request_type = fields.Selection(store=True, related='settlement_id.request_type')
    date_start = fields.Date(string='Start Date')
    date_end = fields.Date(string='End Date')
    amount = fields.Float(string='Amount', digits='Payroll', store=True, related='settlement_id.month_amount')
    paid = fields.Boolean(string='Paid?', store=True, compute='_get_settlement_line_paid')

    def _get_settlement_line_paid(self):
        for rec in self:
            rec.paid = False
            if rec.settlement_id.employee_id and rec.date_start and rec.date_end and rec.settlement_id.settlement_type.rule_id:
                rec.paid = rec._get_settlement_payslip(rec.settlement_id, rec.settlement_id.employee_id, rec.date_start, rec.date_end)

    def _get_settlement_payslip(self, settlement_id, employee_id, date_start, date_end):
        result = False
        payslip_lines = self.env['hr.payslip.line'].sudo().search([
            # ('slip_id.move_id', '!=', False),
            ('slip_id.state', 'not in', ['draft', 'verify', 'cancel', 'refuse']),
            ('slip_id.employee_id', '=', employee_id.id),
            ('salary_rule_id', '=', settlement_id.settlement_type.rule_id.id),
            # ('code', '=', settlement_id.settlement_type.code),
            ('slip_id.date_from', '<=', date_start),
            ('slip_id.date_to', '>=', date_start),
        ]) or False
        if payslip_lines and len(payslip_lines) > 0:
            result = True
        return result

##########################################################################################################################################
#########################################################################################################################################
