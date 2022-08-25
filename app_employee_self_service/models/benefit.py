from odoo import api, fields, models, _
from datetime import datetime

##################################################################################################################################################
###################################################################################################################################################

class BenefitClass(models.Model):
    _name = 'benefit.class'
    _description = "Benefit Class"

    name = fields.Char(string='Benefit Class', copy=False)

##################################################################################################################################################
###################################################################################################################################################

class BenefitType(models.Model):
    _name = 'benefit.type'
    _description = "Benefit Type"

    name = fields.Char(string='Benefit Type', copy=False)

##################################################################################################################################################
###################################################################################################################################################

class BenefitRequest(models.Model):
    _name = 'req.benefit'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _inherits = {'req.self_service': 'req_id'}
    _description = "Benefit Requests"

    req_id = fields.Many2one('req.self_service', string='Request', copy=False, auto_join=True, index=True, ondelete="cascade", required=True)
    source_model = fields.Char(default='req.benefit', related='req_id.source_model', store=True, readonly=False)

    benefit_id = fields.Many2one('benefit.class', string='Benefit', copy=False)
    benefit_type_id = fields.Many2one('benefit.type', string='Benefit Type', copy=False)
    benefit_type = fields.Selection([('Periodical', 'Periodical'), ('non-Periodical', 'non-Periodical'), ('other', 'Other Benefit Based on Project')], string='Type', copy=False)
    benefit_description = fields.Text('Benefit Description', copy=False)
    benefit_purpose = fields.Char('Purpose/Justification', copy=False)

    def unlink(self):
        for rec in self:
            if rec.req_id:
                rec.req_id.unlink()
        return super(BenefitRequest, self).unlink()

    @api.model
    def create(self, vals):
        res = super(BenefitRequest, self).create(vals)
        if res and res.req_id:
            res.req_id.source_id = res.id
        return res

    def write(self, vals):
        res = super(BenefitRequest, self).write(vals)
        for rec in self:
            if rec and rec.req_id:
                rec.req_id.source_id = rec.id
        return res