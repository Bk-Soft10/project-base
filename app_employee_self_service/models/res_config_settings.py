# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from ast import literal_eval


# class ResCompany(models.Model):
#     _inherit = 'res.company'
#
#     service_config = fields.Many2one('hr.service.config', string='Service Config')
#
#
# class ResConfigSettings(models.TransientModel):
#     _inherit = 'res.config.settings'
#
#     service_config = fields.Many2one('hr.service.config', string='Service Config', company_dependent=True, related='company_id.service_config',  readonly=False)

