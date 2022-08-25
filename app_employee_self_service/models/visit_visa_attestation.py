from odoo import api, fields, models, _
from datetime import datetime

##################################################################################################################################################
###################################################################################################################################################

class VisitVisaAttestation(models.Model):
    _name = 'req.visit_visa_attestation'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _inherits = {'req.self_service': 'req_id'}
    _description = "Visit Visa Attestation Requests"

    req_id = fields.Many2one('req.self_service', string='Request', copy=False, auto_join=True, index=True, ondelete="cascade", required=True)
    source_model = fields.Char(default='req.visit_visa_attestation', related='req_id.source_model', store=True, readonly=False)

    request_details = fields.Char('Request Details', copy=False)
    vist_visa_mofa = fields.Binary(string='Visit Visa Request Template', copy=False)

    def unlink(self):
        for rec in self:
            if rec.req_id:
                rec.req_id.unlink()
        return super(VisitVisaAttestation, self).unlink()

    @api.model
    def create(self, vals):
        res = super(VisitVisaAttestation, self).create(vals)
        if res and res.req_id:
            res.req_id.source_id = res.id
        return res

    def write(self, vals):
        res = super(VisitVisaAttestation, self).write(vals)
        for rec in self:
            if rec and rec.req_id:
                rec.req_id.source_id = rec.id
        return res