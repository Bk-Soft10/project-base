from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class PaymentWiz(models.TransientModel):
    _name = 'wiz.payment.loan'

    @api.model
    def _default_partner_id(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', [])
        loans = self.env['hr.loan'].browse(active_ids)
        partner = loans.employee_id.address_home_id.id if loans.employee_id.address_home_id else self.env.user.company_id.partner_id.id
        return partner

    partner_id = fields.Many2one('res.partner', string='Partner', required=True, default=_default_partner_id)
    journal_id = fields.Many2one('account.journal', string='Payment Method', required=True, domain=[('type', 'in', ('bank', 'cash'))])
    company_id = fields.Many2one('res.company', related='journal_id.company_id', string='Company', readonly=True, required=True)
    payment_method_id = fields.Many2one('account.payment.method', string='Payment Type', required=True)
    amount = fields.Monetary(string='Payment Amount', required=True)
    currency_id = fields.Many2one('res.currency', string='Currency', required=True, default=lambda self: self.env.user.company_id.currency_id)
    payment_date = fields.Date(string='Payment Date', default=fields.Date.context_today, required=True)
    communication = fields.Char(string='Memo')
    hide_payment_method = fields.Boolean(compute='_compute_hide_payment_method',
        help="Technical field used to hide the payment method if the selected journal has only one available which is 'manual'")
    loan_id = fields.Many2one('hr.loan', string='Loan Request')

    @api.constrains('amount')
    def _check_amount(self):
        for rec in self:
            if not rec.amount > 0.0:
                raise ValidationError(_('The payment amount must be strictly positive.'))

    @api.depends('journal_id')
    def _compute_hide_payment_method(self):
        for rec in self:
            rec.hide_payment_method = True
            if not rec.journal_id:
                rec.hide_payment_method = True
                return
            journal_payment_methods = rec.journal_id.outbound_payment_method_ids
            rec.hide_payment_method = len(journal_payment_methods) == 1 and journal_payment_methods[0].code == 'manual'

    @api.onchange('loan_id')
    def _change_loan(self):
        for rec in self:
            if rec.loan_id:
                rec.amount = rec.loan_id.loan_amount

    @api.onchange('journal_id')
    def _onchange_journal(self):
        self.ensure_one()
        if self.journal_id:
            # Set default payment method (we consider the first to be the default one)
            payment_methods = self.journal_id.outbound_payment_method_ids
            self.payment_method_id = payment_methods and payment_methods[0] or False
            # Set payment method domain (restrict to methods enabled for the journal and to selected payment type)
            return {'domain': {'payment_method_id': [('payment_type', '=', 'outbound'), ('id', 'in', payment_methods.ids)]}}
        return {}

    def _get_payment_vals(self):
        """ Hook for extension """
        return {
            'partner_type': 'supplier',
            'payment_type': 'outbound',
            'partner_id': self.partner_id.id,
            'journal_id': self.journal_id.id,
            'company_id': self.company_id.id,
            'loan_id': self.loan_id.id,
            'payment_method_id': self.payment_method_id.id,
            'amount': self.amount,
            'currency_id': self.currency_id.id,
            'payment_date': self.payment_date,
            'communication': self.communication,
            'writeoff_label': 'Loan Payment',
        }

    def create_payment(self):
        for rec in self:
            payment_opj = self.env['account.payment'].sudo()
            if rec.loan_id and rec.journal_id and rec.amount:
                payment_dict = rec._get_payment_vals()
                payment_created = payment_opj.create(payment_dict)
                if payment_created and rec.loan_id.category_id and rec.loan_id.category_id.employee_account_id:
                    payment_created.write({'destination_account_id': rec.loan_id.category_id.employee_account_id.id})
                    payment_created.post()
