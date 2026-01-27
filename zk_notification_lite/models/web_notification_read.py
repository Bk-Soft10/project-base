# -*- coding: utf-8 -*-
from odoo import models, fields


class WebNotificationRead(models.Model):
    _name = 'web.notification.read'
    _description = 'Web Notification Read Status'
    _rec_name = 'notification_id'

    notification_id = fields.Many2one(
        'web.notification',
        string='Notification',
        required=True,
        ondelete='cascade'
    )
    user_id = fields.Many2one(
        'res.users',
        string='User',
        required=True,
        ondelete='cascade',
        default=lambda self: self.env.user
    )
    read_date = fields.Datetime(
        string='Read Date',
        default=fields.Datetime.now
    )

    _sql_constraints = [
        ('unique_notification_user', 'unique(notification_id, user_id)',
         'A user can only mark a notification as read once!')
    ]
