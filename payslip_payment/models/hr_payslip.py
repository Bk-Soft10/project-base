# -*- coding: utf-8 -*-
import logging
import pytz
import time
import babel

from odoo import _, api, fields, models, tools, _
# from odoo.addons.mail.models.mail_template import format_tz
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.translate import html_translate

from datetime import datetime
from datetime import time as datetime_time
from dateutil import relativedelta
from odoo.tools import float_compare, float_is_zero

_logger = logging.getLogger(__name__)

class HrPayslip(models.Model):
    _name = 'hr.payslip'
    _inherit = ['hr.payslip', 'mail.thread']

    state = fields.Selection(selection_add=[
        ('paid', 'Paid'),
    ], string='Status', index=True, readonly=True, copy=False, default='draft',
        help="""* When the payslip is created the status is \'Draft\'
                \n* If the payslip is under verification, the status is \'Waiting\'.
                \n* If the payslip is confirmed then status is set to \'Done\'.
                \n* When user cancel payslip the status is \'Rejected\'.""", track_visibility='onchange')
    total_amount = fields.Float(string='Total Amount', compute='_compute_total_amount', store=True)

    @api.depends('line_ids')
    @api.onchange('line_ids')
    def _compute_total_amount(self):
        for slip in self:
            total_amount_new = 0.0
            if slip.line_ids and len(slip.line_ids) > 1:
                for line in slip.line_ids:
                    if line.salary_rule_id.code == 'NET':
                        total_amount_new += line.total
            elif slip.line_ids and len(slip.line_ids) == 1:
                for line in slip.line_ids:
                    total_amount_new += line.total
            slip.total_amount = total_amount_new

    ##@api.multi
    def set_to_paid(self):
        self.write({'state': 'paid'})

    def action_payslip_done(self):
        for rec in self:
            if rec.total_amount == 0:
                rec.state = 'done'
            else:
                super(HrPayslip, self).action_payslip_done()

class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'

    state = fields.Selection(selection_add=[
        ('done', 'Confirmed'),
        ('paid', 'Paid'),
    ], string='Status', index=True, readonly=True, copy=False, default='draft')
    total_amount = fields.Float(string='Total Amount', compute='_compute_total_amount')

    @api.depends('slip_ids')
    @api.onchange('slip_ids')
    def _compute_total_amount(self):
        for rec in self:
            total_amount_new = 0.0
            for slip in rec.slip_ids:
                for line in slip.line_ids:
                    if line.salary_rule_id.code == 'NET':
                        total_amount_new += line.total
                slip.total_amount = total_amount_new
            rec.total_amount = total_amount_new

    ##@api.multi
    def batch_wise_payslip_confirm(self):
        for rec in self:
            for record in rec.slip_ids:
                if record.state == 'draft':
                    record.action_payslip_done()
            rec.state = 'done'
    def close_payslip_run(self):
        self.batch_wise_payslip_confirm()
        return super(HrPayslipRun, self).close_payslip_run()

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    payslip_id = fields.Many2one('hr.payslip', string='Expense', copy=False, help="Expense where the move line come from")

    ##@api.multi
    def reconcile(self, writeoff_acc_id=False, writeoff_journal_id=False):
        #_get_matched_percentage
        res = super(AccountMoveLine, self).reconcile(writeoff_acc_id=writeoff_acc_id, writeoff_journal_id=writeoff_journal_id)
        for rec in self:
            rec.payslip_id.set_to_paid()
        #account_move_ids = [l.move_id.id for l in self if float_compare(l.move_id.matched_percentage, 1, precision_digits=5) == 0]
        account_move_ids = [l.move_id.id for l in self if float_compare(l.move_id._get_cash_basis_matched_percentage(), 1, precision_digits=5) == 0]
        if account_move_ids:
            payslip = self.env['hr.payslip'].search([
                ('move_id', 'in', account_move_ids), ('state', '=', 'done')
            ])
            payslip.set_to_paid()
        return res
