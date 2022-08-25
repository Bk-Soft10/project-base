from odoo import api, fields, models, _
from datetime import datetime

##################################################################################################################################################
###################################################################################################################################################

class ChangingResidencyJobTitle(models.Model):
    _name = 'req.changing_residency_job'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _inherits = {'req.self_service': 'req_id'}
    _description = "Changing Residency Job Title Requests"

    req_id = fields.Many2one('req.self_service', string='Request', copy=False, auto_join=True, index=True, ondelete="cascade", required=True)
    source_model = fields.Char(default='req.changing_residency_job', related='req_id.source_model', store=True, readonly=False)

    job_title = fields.Char('New Job Title', copy=False)
    reason_change_job = fields.Text('Reason for changing job title', copy=False)

    def unlink(self):
        for rec in self:
            if rec.req_id:
                rec.req_id.unlink()
        return super(ChangingResidencyJobTitle, self).unlink()

    @api.model
    def create(self, vals):
        res = super(ChangingResidencyJobTitle, self).create(vals)
        if res and res.req_id:
            res.req_id.source_id = res.id
        return res

    def write(self, vals):
        res = super(ChangingResidencyJobTitle, self).write(vals)
        for rec in self:
            if rec and rec.req_id:
                rec.req_id.source_id = rec.id
        return res