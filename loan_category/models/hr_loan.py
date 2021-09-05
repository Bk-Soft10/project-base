from odoo import models, fields, api, _
from odoo.exceptions import except_orm, Warning ,UserError, ValidationError
from datetime import datetime
import odoo.addons.decimal_precision as dp
from odoo.tools.float_utils import float_round, float_compare
import time
from odoo import models, api, fields
from odoo.exceptions import UserError



class AccountPayment(models.Model):
    _inherit = 'account.payment'

    loan_id = fields.Many2one('hr.loan', string="Loan Request")



class HrLoan(models.Model):
    _inherit = 'hr.loan'

    category_id = fields.Many2one('loan.category', string="Loan Category")
    payment_ids = fields.One2many('account.payment', 'loan_id', string='Payment List')
    payment = fields.Boolean('Have Payment', store=True, related='category_id.payment', readonly=1)
    # payment_id = fields.Many2one('account.payment')

    @api.onchange('category_id')
    def _onchange_category(self):
        for rec in self:
            if rec.category_id:
                rec.employee_account_id = rec.category_id.employee_account_id.id
                rec.journal_id = rec.category_id.journal_id.id
                rec.treasury_account_id = rec.category_id.treasury_account_id.id

    # def action_approve(self):
    #     super(HrLoan, self).action_approve()
    #     loan_approve = self.env['ir.config_parameter'].sudo().get_param('account.loan_approve')
    #     for rec in self:
    #         if not loan_approve and rec.category_id and rec.category_id.payment_journal_id and rec.category_id.payment == True:
    #             payment_methods = self.journal_id.outbound_payment_method_ids
    #             payment_created = self.env['account.payment'].sudo().create({
    #                 'partner_id': rec.employee_id.address_home_id.id if rec.employee_id.address_home_id else self.env.user.company_id.partner_id.id,
    #                 'partner_type': 'supplier',
    #                 'payment_type': 'outbound',
    #                 'journal_id': rec.category_id.payment_journal_id.id,
    #                 'payment_method_id': payment_methods and payment_methods[0] or False,
    #                 'amount': rec.loan_amount,
    #                 'payment_date': rec.date,
    #                 'writeoff_label': 'Loan Payment',
    #                 'destination_account_id': rec.category_id.employee_account_id.id
    #             })
    #             if payment_created:
    #                 payment_created.write({'destination_account_id': rec.category_id.employee_account_id.id})
    #                 payment_created.post()
    #                 rec.payment_id = payment_created.id
    #
    # def action_double_approve(self):
    #     super(HrLoan, self).action_double_approve()
    #     for rec in self:
    #         if rec.category_id and rec.category_id.payment_journal_id and rec.category_id.payment == True:
    #             payment_methods = self.journal_id.outbound_payment_method_ids
    #             payment_created = self.env['account.payment'].sudo().create({
    #                 'partner_id': rec.employee_id.address_home_id.id if rec.employee_id.address_home_id else self.env.user.company_id.partner_id.id,
    #                 'partner_type': 'supplier',
    #                 'payment_type': 'outbound',
    #                 'journal_id': rec.category_id.payment_journal_id.id,
    #                 'payment_method_id': payment_methods and payment_methods[0] or False,
    #                 'amount': rec.loan_amount,
    #                 'payment_date': rec.date,
    #                 'writeoff_label': 'Loan Payment',
    #                 'destination_account_id': rec.category_id.employee_account_id.id
    #             })
    #             if payment_created:
    #                 payment_created.write({'destination_account_id': rec.category_id.employee_account_id.id})
    #                 payment_created.post()
    #                 rec.payment_id = payment_created.id

class CategoryLoan(models.Model):
    _name = 'loan.category'

    name = fields.Char(string="Name")
    employee_account_id = fields.Many2one('account.account', string="Loan Account")
    treasury_account_id = fields.Many2one('account.account', string="Treasury Account")
    journal_id = fields.Many2one('account.journal', string="Journal")
    # payment_journal_id = fields.Many2one('account.journal', string="Journal", domain=[('type', 'in', ['bank', 'cash'])])
    payment = fields.Boolean('Have Payment')




