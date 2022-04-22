
import logging
import pytz
import time
import babel

from odoo import _, api, fields, models, tools, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.translate import html_translate

from datetime import datetime
from datetime import time as datetime_time
from dateutil import relativedelta
from odoo.tools import float_compare, float_is_zero

_logger = logging.getLogger(__name__)

class AccountPayment(models.Model):
    _inherit = 'account.payment'
    payslip_payment = fields.Boolean(string='Payslip?')
    # payslip_journal = fields.Many2one('account.journal', string='Payslip Journal')
    payslip_account_id = fields.Many2one('account.account', string='Payslip Account')
    payslip_id = fields.Many2one('hr.payslip', string='Employee Payslip')
    payslip_batch_id = fields.Many2one('hr.payslip.run', string='Payslip Batch')

    @api.depends('invoice_ids', 'payment_type', 'partner_type', 'partner_id')
    def _compute_destination_account_id(self):
        super(AccountPayment, self)._compute_destination_account_id()
        for payment in self:
            if payment.payslip_payment and payment.payslip_account_id:
                payment.destination_account_id = payment.payslip_account_id.id