from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)


class DocumentData(models.Model):
    _inherit = 'hr.applicant'
    
    document_file = fields.Binary('Document File')
    degree = fields.Char("Degree")
    location = fields.Char("Location")
    skills = fields.Many2many('hr.applicant.skills', string="Skills")
    date_of_birth = fields.Date("Date Of Birth")
    marital_status = fields.Selection([('single', 'Single'), ('married', 'Married'), ('not mentioned', 'Not Mentioned')])
    gender = fields.Selection([('male', 'Male'), ('female', 'Female'), ('not mentioned', 'Not Mentioned')])
    experience_years = fields.Selection([(str(i), str(i)) for i in range(51)], string="Experience")
    experience_months = fields.Selection([(str(i), str(i)) for i in range(12)], string="Experience Months")
    languages = fields.Many2many('hr.applicant.language', string="Languages")

    @api.model
    def document_file_create(self, value, name, model):

        data = value.split('base64')[1] if value else False

        record = self.env['upload.wizard'].create({
            'name': name,
            'file_name': name,
            'file_data': data,
        })
        self.env['upload.wizard'].action_ocr_resume(record)

