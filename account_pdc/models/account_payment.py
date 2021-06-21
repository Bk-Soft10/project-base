# -*- coding: utf-8 -*-

from odoo import models, fields, api,tools, _
from odoo.exceptions import UserError, except_orm

class AccountJournal(models.Model):
    _inherit = 'account.journal'
    is_check_journal = fields.Boolean('Check Journal')

class account_payment(models.Model):
    _inherit = 'account.payment'

    check_ref = fields.Char('Reference')
    check_date = fields.Date('Maturity Date')
    check_note = fields.Char('about Check')
    check_journal_id = fields.Many2one('account.journal', 'Clearing Journal', domain=[('type', 'in', ('bank', 'cash')), ('is_check_journal','!=', True)])
    is_check_journal = fields.Boolean(related='journal_id.is_check_journal')
    # active = fields.Boolean()
    state = fields.Selection([('draft', 'Draft'), ('posted', 'Posted'), ('sent', 'Sent'), ('reconciled', 'Reconciled'),('cancel','Cancelled')],
                             readonly=True, default='draft', copy=False, string="Status")

    @api.depends('journal_id','currency_id')
    def compute_pdc_journal(self):
        company_currency = self.env.user.company_id.currency_id


        for rec in self:
            if not rec.journal_id or not rec.currency_id:
                continue
            if rec.journal_id and rec.journal_id.is_check_journal and rec.currency_id.id == company_currency.id:
                rec.is_check_journal = True

    def post(self):
        PDC = self.env['account.pdc']
        posted = super(account_payment, self).post()
        company_currency = self.env.user.company_id.currency_id
        for rec in self:
            if rec.is_check_journal:
                PDC.create({
                    'name': rec.check_ref,
                    'maturity_date': rec.check_date,
                    'check_note': rec.check_note,
                    'journal_id': rec.check_journal_id.id if rec.check_journal_id else False,
                    'type': 'customer' if rec.payment_type == 'inbound' else 'vendor',
                    'payment_id': rec.id,
                    'partner_id': rec.partner_id.id,
                    'currency_id': company_currency.id,
                    'amount': rec.amount,
                })
