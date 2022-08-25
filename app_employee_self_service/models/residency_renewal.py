from odoo import api, fields, models, _
from datetime import datetime

##################################################################################################################################################
###################################################################################################################################################

class ResidencyRenewal(models.Model):
    _name = 'req.residency_renewal'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _inherits = {'req.self_service': 'req_id'}
    _description = "Residency (Iqama) Renewal Requests"

    req_id = fields.Many2one('req.self_service', string='Request', copy=False, auto_join=True, index=True, ondelete="cascade", required=True)
    source_model = fields.Char(default='req.residency_renewal', related='req_id.source_model', store=True, readonly=False)

    renewal_justification = fields.Char('Renewal Justification', copy=False)
    pending_fees = fields.Boolean(string='Associates Fees are Paid', copy=False)

    def unlink(self):
        for rec in self:
            if rec.req_id:
                rec.req_id.unlink()
        return super(ResidencyRenewal, self).unlink()

    @api.model
    def create(self, vals):
        res = super(ResidencyRenewal, self).create(vals)
        if res and res.req_id:
            res.req_id.source_id = res.id
        return res

    def write(self, vals):
        res = super(ResidencyRenewal, self).write(vals)
        for rec in self:
            if rec and rec.req_id:
                rec.req_id.source_id = rec.id
        return res