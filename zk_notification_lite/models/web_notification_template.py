# -*- coding: utf-8 -*-
from odoo import models, fields

class WebNotificationTemplate(models.Model):
    _name = 'web.notification.template'
    _description = 'Web Notification Template'

    name = fields.Char(string='Template Name', required=True)
    message = fields.Text(string='Message', required=True)
