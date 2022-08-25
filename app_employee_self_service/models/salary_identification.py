from odoo import api, fields, models, _
from datetime import datetime

##################################################################################################################################################
###################################################################################################################################################

class SalaryIdentification(models.Model):
    _name = 'req.salary_identification'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _inherits = {'req.self_service': 'req_id'}
    _description = "Salary Identification Requests"

    req_id = fields.Many2one('req.self_service', string='Request', copy=False, auto_join=True, index=True, ondelete="cascade", required=True)
    source_model = fields.Char(default='req.salary_identification', related='req_id.source_model', store=True, readonly=False)

    to_who = fields.Char('To Who', copy=False, default=_("whom it may concern"))

    def unlink(self):
        for rec in self:
            if rec.req_id:
                rec.req_id.unlink()
        return super(SalaryIdentification, self).unlink()

    @api.model
    def create(self, vals):
        res = super(SalaryIdentification, self).create(vals)
        if res and res.req_id:
            res.req_id.source_id = res.id
        return res

    def write(self, vals):
        res = super(SalaryIdentification, self).write(vals)
        for rec in self:
            if rec and rec.req_id:
                rec.req_id.source_id = rec.id
        return res