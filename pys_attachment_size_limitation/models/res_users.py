# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ResUsers(models.Model):
    _inherit = 'res.users'

    users_general_size_limit_attachment = fields.Integer(string="Attachment Size Limit",
                                                 help="Maximum allowed attachment size",
                                                 store=True,
                                                 config_parameter="pys_attachment_size_limitation.users_general_size_limit_attachment"
                                                 )

    user_select_attachment_size_unit = fields.Selection([('mb', 'MB'), ('kb', 'KB')],
                                                   string="Attachment Size Unit", store=True,
                                                   help="Select the unit used for attachment size limitation",
                                                   default='kb')

    @api.constrains('users_general_size_limit_attachment')
    def _check_positive_attachment_size(self):
        for rec in self:
            if rec.users_general_size_limit_attachment is not None and rec.users_general_size_limit_attachment < 0:
                raise ValidationError(
                    _("Attachment size limit must be a positive value.")
                )
