from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import math, random
from odoo.http import request

##################################################################################################################################################
###################################################################################################################################################

class OTPCode(models.Model):
    _name = 'salary_transfer.otp.code'
    _description = "OTP Code"

    code = fields.Char('Code', copy=False)
    salary_transfer_id = fields.Many2one('req.salary_transfer', string='Salary Transfer Request', copy=False)
    exp_date = fields.Datetime('Expired Date', copy=False)

    @api.model
    def generateOTP(self):
        digits = "0123456789"
        OTP = ""

        for i in range(4):
            OTP += digits[math.floor(random.random() * 10)]

        return OTP

    def send_otp_code(self):
        self.ensure_one()
        email_templ = self.env.ref('app_employee_self_service.email_salary_transfer_otp_code', raise_if_not_found=False) or False
        partner_ids = [self.env.user.partner_id]
        if partner_ids and email_templ and self.salary_transfer_id and self.salary_transfer_id.req_id:
            self.salary_transfer_id.req_id.send_email(self.id, email_templ, partner_ids)

##################################################################################################################################################
###################################################################################################################################################

class SalaryTransfer(models.Model):
    _name = 'req.salary_transfer'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _inherits = {'req.self_service': 'req_id'}
    _description = "Salary Transfer Requests"

    req_id = fields.Many2one('req.self_service', string='Request', copy=False, auto_join=True, index=True, ondelete="cascade", required=True)
    source_model = fields.Char(default='req.salary_transfer', related='req_id.source_model', store=True, readonly=False)

    country_id = fields.Many2one('res.country', string='Country', copy=False, required=True, default=lambda self: self.env.company.country_id)
    bank_id = fields.Many2one('res.bank', string='Bank', copy=False, required=True)
    iban = fields.Char('IBan', copy=False, default='Sa', required=True)
    iban_confirm = fields.Char('IBan Re-enter', copy=False, default='Sa', required=True)
    otp_code_ids = fields.One2many('salary_transfer.otp.code', 'salary_transfer_id', string='OTP List', copy=False)

    enter_otp_code = fields.Char('OTP Code', copy=False)

    otp_code = fields.Char('OTP Code', copy=False)
    exp_date = fields.Datetime('Expired Date', copy=False)
    otp_valid = fields.Boolean(string='OTP Valid', copy=False)

    def _create_otp_code(self):
        otp_code_obj = self.env['salary_transfer.otp.code']
        for rec in self:
            OTP = otp_code_obj.generateOTP()
            exp_date = datetime.now() + relativedelta(minutes=15)
            if OTP:
                otp_vals = {
                    'code': OTP,
                    'exp_date': exp_date,
                    'salary_transfer_id': rec.id
                }
                new_otp = otp_code_obj.sudo().create(otp_vals)
                if new_otp:
                    new_otp.send_otp_code()
                    rec.otp_code = OTP
                    rec.exp_date = exp_date

    def send_otp_code(self):
        for rec in self:
            if not rec.otp_code_ids or len(rec.otp_code_ids.ids) < 3:
                rec._create_otp_code()

    @api.model
    def _check_otp_code(self, salary_transfer, otp_code):
        if salary_transfer and salary_transfer.otp_code and otp_code and salary_transfer.exp_date and salary_transfer.otp_code == otp_code and salary_transfer.exp_date >= datetime.now():
            salary_transfer.otp_valid = True
            return True
        else:
            return False

    @api.constrains('iban', 'iban_confirm')
    def _check_amount(self):
        for rec in self:
            if rec.iban != rec.iban_confirm:
                raise ValidationError(_('Please Re-check Iban Number'))

    def unlink(self):
        for rec in self:
            if rec.req_id:
                rec.req_id.unlink()
        return super(SalaryTransfer, self).unlink()

    @api.model
    def create(self, vals):
        res = super(SalaryTransfer, self).create(vals)
        if res and res.req_id:
            res.req_id.source_id = res.id
        return res

    def write(self, vals):
        res = super(SalaryTransfer, self).write(vals)
        for rec in self:
            if rec and rec.req_id:
                rec.req_id.source_id = rec.id
        return res