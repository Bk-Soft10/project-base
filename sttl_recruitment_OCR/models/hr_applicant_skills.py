from odoo import models, fields, api, _
from random import randint


class hrApplicantSkills(models.Model):
    _name = 'hr.applicant.skills'
    _description = 'To add the skills in the hr.applicant model'


    def _get_default_color(self):
        return randint(1, 11)

    name = fields.Char(string='Skill Name', required=True, unique=True)
    color = fields.Integer(string='Color Index' , default= _get_default_color)
