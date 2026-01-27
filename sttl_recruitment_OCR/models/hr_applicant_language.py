# models/language.py
from odoo import models, fields
from random import randint


class ApplicantLanguage(models.Model):
    _name = 'hr.applicant.language'
    _description = 'Applicant Language'

    def _get_default_color(self):
        return randint(1, 11)

    name = fields.Char("Language", required=True)
    color = fields.Integer(string='Color Index', default=_get_default_color)
