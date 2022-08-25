# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from datetime import datetime, date
from odoo.exceptions import AccessError, UserError, ValidationError


class ExpanseWizard(models.TransientModel):
    _name = 'expanse.req.wizard'
    _description = 'Expanse Req Wizard'

    req_id = fields.Many2one('req.self_service', string='Request', copy=False)
    expense_amount = fields.Float('Amount')

    def create_expanse(self):
        pass