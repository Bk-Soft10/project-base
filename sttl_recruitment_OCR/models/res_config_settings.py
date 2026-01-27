from odoo import api, fields, models, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    qwen_api_key = fields.Char(config_parameter='sttl_recruitment_OCR.qwen_api_key', string="Qwen API key")