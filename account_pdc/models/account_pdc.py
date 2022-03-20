# -*- coding: utf-8 -*-
import datetime

from odoo import models, fields, api,tools, _
from odoo.exceptions import UserError, ValidationError, except_orm

class AccountPDC(models.Model):
    _name = 'account.pdc'
    _inherit = ['mail.thread']
    _description = "PDC"
    _order = 'maturity_date desc'

    name = fields.Char('Reference')
    check_note = fields.Char('about Check')
    type = fields.Selection([('customer', 'Customer'), ('vendor', 'Vendor')])
    maturity_date = fields.Date('Maturity Date')
    partner_id = fields.Many2one('res.partner', 'Partner')
    journal_id = fields.Many2one('account.journal', 'Clearing Journal', domain=[('type', 'in', ('bank', 'cash')), ('is_check_journal','!=', True)])
    payment_id = fields.Many2one('account.payment', 'Payment')
    state = fields.Selection([('draft', 'New'), ('reject', 'Rejected'), ('clear', 'Cleared')], default='draft', track_visibility="onchange")
    amount = fields.Monetary()
    currency_id = fields.Many2one('res.currency', "Currency")
    move_id = fields.Many2one('account.move', "Journal Entry")
    company_id = fields.Many2one('res.company', "Company", default=lambda self: self.env.user.company_id)
    note = fields.Text()
    with_check_date = fields.Boolean('Use Check Date')

    @api.model
    def update_pdc_move(self):
        pdc_ids = self.env['account.pdc'].sudo().search([('state', '=', 'clear'), ('move_id', '!=', False)])
        for pdc in pdc_ids:
            if pdc.move_id.date != pdc.maturity_date:
                pdc.move_id.date = pdc.maturity_date


    def clear(self):
        self.ensure_one()
        AccountMove = self.env['account.move']
        AccountMoveLine = self.env['account.move.line'].with_context(check_move_validity=False)
        if not self.journal_id:
            raise ValidationError('Select Clearing Journal')
        move_vals = {
            'journal_id': self.journal_id.id,
            'ref': 'Check Clearing: ' + self.name
        }
        today_date = datetime.date.today()
        # print(datetime.date(self.maturity_date.year, self.maturity_date.month, self.maturity_date.day))
        # print(datetime.date(today_date.year, today_date.month, today_date.day))
        if self.maturity_date and datetime.date(self.maturity_date.year, self.maturity_date.month, self.maturity_date.day) <= datetime.date(today_date.year, today_date.month, today_date.day):
        # if self.maturity_date:
            if self.with_check_date == True:
                move_vals['date'] = self.maturity_date
            Move = AccountMove.create(move_vals)
            debit_line = {}
            credit_line = {}
            if self.type == 'customer':
                debit_line['account_id'] = self.journal_id.default_debit_account_id.id
                credit_line['account_id'] = self.payment_id.journal_id.default_credit_account_id.id
            else:
                credit_line['account_id'] = self.journal_id.default_credit_account_id.id
                debit_line['account_id'] = self.payment_id.journal_id.default_debit_account_id.id

            debit_line['partner_id'] = self.partner_id.id
            debit_line['name'] = 'Check Clearing: ' + self.name
            debit_line['debit'] = self.amount
            debit_line['credit'] = 0.0
            debit_line['move_id'] = Move.id

            credit_line['partner_id'] = self.partner_id.id
            credit_line['name'] = 'Check Clearing: ' + self.name
            credit_line['debit'] = 0.0
            credit_line['credit'] = self.amount
            credit_line['move_id'] = Move.id

            AccountMoveLine.create(debit_line)
            AccountMoveLine.create(credit_line)
            Move.post()
            self.state = 'clear'
            self.move_id = Move.id
            # if self.with_check_date == True and self.move_id:
            #     self.move_id.date = self.maturity_date
        else:
            raise ValidationError(_("Error in Check Date"))


    def reject(self):
        self.ensure_one()
        partner_account = False
        if self.type == 'customer':
            partner_account = self.payment_id.partner_id.property_account_receivable_id
        else:
            partner_account = self.payment_id.partner_id.property_account_payable_id
        #
        # for move in self.payment_id.move_line_ids.mapped('move_id'):
        #     move._reverse_moves()
        #     reversal_move_id = self.env['account.move'].search([('reversed_entry_id', '=', move.id)])
        #
        #     reversal_move_id.post()
        #     move.line_ids.sudo().remove_move_reconcile()
        #     raise UserError(self.payment_id.move_line_ids.filtered(lambda r: r.account_id == partner_account))
        #     self.payment_id.move_line_ids.filtered(lambda r: r.account_id == partner_account).reconcile()
        # self.payment_id.state = 'cancel'
        # self.state = 'reject'

        reverse_id = 0

        for move in self.payment_id.move_line_ids.mapped('move_id'):
            # if self.payment_id.invoice_ids:
            move.line_ids.sudo().remove_move_reconcile()
            move._reverse_moves()
            reverse_id = self.env['account.move'].search([('reversed_entry_id', '=', move.id)])
            to_reconcile = self.env['account.move.line'].search([('move_id', 'in', [move.id, reverse_id.id]), ('account_id', '=', partner_account.id)])
            to_reconcile.reconcile()
            for l in move.line_ids:
                l.payment_id = False
            self.move_id = reverse_id

        self.payment_id.state = 'draft'
        self.move_id = reverse_id
        self.payment_id.cancel()
        # self.move_id.button_cancel()
        self.move_id.post()
        self.state = "reject"
