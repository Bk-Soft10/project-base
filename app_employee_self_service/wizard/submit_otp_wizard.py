# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from datetime import datetime, date
from odoo.exceptions import AccessError, UserError, ValidationError


class OTPWizard(models.TransientModel):
    _name = 'submit.otp.wizard'
    _description = 'Submit OTP Wizard'

    enter_otp_code = fields.Char('OTP', copy=False)
    salary_transfer_id = fields.Many2one('req.salary_transfer', string='Salary Transfer Request', copy=False)

    def resend_otp(self):
        for rec in self:
            if rec.salary_transfer_id:
                rec.salary_transfer_id.send_otp_code()

    def validate_otp(self):
        for rec in self:
            result = False
            if rec.salary_transfer_id and rec.enter_otp_code:
                result = self.env['req.salary_transfer'].sudo()._check_otp_code(rec.salary_transfer_id, rec.enter_otp_code)
                if result == False or not result:
                    raise ValidationError(_("Wrong OTP Code . Try Again"))
            if result:
                return {'type': 'ir.actions.act_window_close'}