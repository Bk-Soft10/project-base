# -*- coding: utf-8 -*-
from odoo import models, fields


class ResUsers(models.Model):
    _inherit = 'res.users'

    allowed_manage_web_notifications = fields.Boolean(
        string='Allowed to create and Manages Web Notifications',
        default=False,
        help='Allow this user to create and manage web notifications'
    )
