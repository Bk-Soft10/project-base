
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    module_payslip_payment_journal = fields.Boolean(string='Payment as Journal Entry')

    payslip_direct_journal = fields.Boolean(string='Payslip Journal Account')

    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res.update(
            module_payslip_payment_journal = bool(self.env['ir.config_parameter'].sudo().get_param('payslip_payment.module_payslip_payment_journal')),
            payslip_direct_journal = bool(self.env['ir.config_parameter'].sudo().get_param('payslip_payment.payslip_direct_journal')),
        )
        return res

    def set_values(self):
        self.env['ir.config_parameter'].sudo().set_param('payslip_payment.module_payslip_payment_journal',bool(self.module_payslip_payment_journal))
        self.env['ir.config_parameter'].sudo().set_param('payslip_payment.payslip_direct_journal',bool(self.payslip_direct_journal))
        super(ResConfigSettings, self).set_values()


    @api.onchange('module_payslip_payment_journal')
    def onchange_module_payslip_payment_journal(self):
        if self.module_payslip_payment_journal:
            self.module_payslip_payment = True


    @api.onchange('payslip_direct_journal')
    def onchange_payslip_direct_journal(self):
        if self.payslip_direct_journal:
            self.module_payslip_payment = True
