from odoo import api, fields, models, _
from datetime import datetime

##################################################################################################################################################
###################################################################################################################################################

class SalaryConfirmation(models.Model):
    _name = 'req.salary_confirmation'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _inherits = {'req.self_service': 'req_id'}
    _description = "Salary Confirmation Requests"

    req_id = fields.Many2one('req.self_service', string='Request', copy=False, auto_join=True, index=True, ondelete="cascade", required=True)
    source_model = fields.Char(default='req.salary_confirmation', related='req_id.source_model', store=True, readonly=False)

    country_id = fields.Many2one('res.country', string='Country', copy=False, required=True, default=lambda self: self.env.company.country_id)
    bank_id = fields.Many2one('res.bank', string='Bank', copy=False)

    def unlink(self):
        for rec in self:
            if rec.req_id:
                rec.req_id.unlink()
        return super(SalaryConfirmation, self).unlink()

    @api.model
    def create(self, vals):
        res = super(SalaryConfirmation, self).create(vals)
        if res and res.req_id:
            res.req_id.source_id = res.id
        return res

    def write(self, vals):
        res = super(SalaryConfirmation, self).write(vals)
        for rec in self:
            if rec and rec.req_id:
                rec.req_id.source_id = rec.id
        return res