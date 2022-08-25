from odoo import api, fields, models, _
from datetime import datetime
from odoo.exceptions import ValidationError

##################################################################################################################################################
###################################################################################################################################################

class VisaExitReturn(models.Model):
    _name = 'req.visa_exit_return'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _inherits = {'req.self_service': 'req_id'}
    _description = "Exit and Re-entry Visa Requests"

    req_id = fields.Many2one('req.self_service', string='Request', copy=False, auto_join=True, index=True, ondelete="cascade", required=True)
    source_model = fields.Char(default='req.visa_exit_return', related='req_id.source_model', store=True, readonly=False)

    purpose = fields.Char('Purpose', copy=False)
    visa_type = fields.Selection([('single', 'Single'), ('multiple', 'Multiple')], string='Visa Type', copy=False, default='single')
    by_company = fields.Boolean(string='By Company', copy=False)
    cost_project = fields.Boolean(string='Cost on Project', copy=False)
    date_from = fields.Date(string='From', copy=False)
    date_to = fields.Date(string='To', copy=False)


    @api.constrains('date_from', 'date_to')
    def _check_date(self):
        for rec in self:
            if rec.date_from and rec.date_to and rec.date_from > rec.date_to:
                raise ValidationError(_('Re-check Dates From/TO'))

    def unlink(self):
        for rec in self:
            if rec.req_id:
                rec.req_id.unlink()
        return super(VisaExitReturn, self).unlink()

    @api.model
    def create(self, vals):
        res = super(VisaExitReturn, self).create(vals)
        if res and res.req_id:
            res.req_id.source_id = res.id
        return res

    def write(self, vals):
        res = super(VisaExitReturn, self).write(vals)
        for rec in self:
            if rec and rec.req_id:
                rec.req_id.source_id = rec.id
        return res