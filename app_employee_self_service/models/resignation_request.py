from odoo import api, fields, models, _
from datetime import datetime, date, timedelta, time
from pytz import timezone, UTC
from odoo.addons.resource.models.resource import float_to_time, HOURS_PER_DAY
from odoo.exceptions import ValidationError

##################################################################################################################################################
###################################################################################################################################################

class ResignationReason(models.Model):
    _name = 'resignation.reason'
    _description = "Resignation Reasons"

    name = fields.Char(string='Reason', copy=False)
    resignation_description = fields.Text('Resignation Reason Description', copy=False)

##################################################################################################################################################
###################################################################################################################################################

class ResignationRequest(models.Model):
    _name = 'req.resignation_request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _inherits = {'req.self_service': 'req_id'}
    _description = "Resignation Requests"

    req_id = fields.Many2one('req.self_service', string='Request', copy=False, auto_join=True, index=True, ondelete="cascade", required=True)
    source_model = fields.Char(default='req.resignation_request', related='req_id.source_model', store=True, readonly=False)

    resignation_reason = fields.Many2one('resignation.reason', string='Resignation Reason', copy=False, required=True)
    resignation_description = fields.Text('Resignation Reason Description', copy=False)
    last_day = fields.Date(string='Last Working Day', copy=False)

    def unlink(self):
        for rec in self:
            if rec.req_id:
                rec.req_id.unlink()
        return super(ResignationRequest, self).unlink()

    @api.model
    def create(self, vals):
        res = super(ResignationRequest, self).create(vals)
        if res and res.req_id:
            res.req_id.source_id = res.id
        return res

    def write(self, vals):
        res = super(ResignationRequest, self).write(vals)
        for rec in self:
            if rec and rec.req_id:
                rec.req_id.source_id = rec.id
        return res