# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    enable_general_size_limit_attachment = fields.Boolean(string="Enable Attachment Size Limitation",
                                                          help='Enable Attachment Size Limitation',
                                                          store=True,
                                                          config_parameter="pys_attachment_size_limitation.enable_general_size_limit_attachment"
                                                          )

    general_size_limit_attachment = fields.Integer(string="Attachment Size Limit",
                                                   help="Maximum allowed attachment size",
                                                   store=True,
                                                   config_parameter="pys_attachment_size_limitation.general_size_limit_attachment"
                                                   )

    select_attachment_size_unit = fields.Selection([('mb', 'MB'), ('kb', 'KB')],
                                                   string="Attachment Size Unit",
                                                   help="Select the unit used for attachment size limitation",
                                                   config_parameter="pys_attachment_size_limitation.select_attachment_size_unit",
                                                   store=True, default='kb'
                                                   )

    @api.constrains('general_size_limit_attachment')
    def _check_positive_attachment_size(self):
        for rec in self:
            if rec.general_size_limit_attachment is not None and rec.general_size_limit_attachment < 0:
                raise ValidationError(
                    _("Attachment size limit must be a positive value.")
                )
