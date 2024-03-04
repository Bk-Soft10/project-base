# -*- coding: utf-8 -*-

from odoo import _, api, exceptions, fields, models, modules


class Users(models.Model):
    """ Update of res.users class
        - add a preference about sending emails about notifications
        - make a new user follow itself
        - add a welcome message
        - add suggestion preference
        - if adding groups to a user, check mail.channels linked to this user
          group, and the user. This is done by overriding the write method.
    """
    _name = 'res.users'
    _inherit = ['res.users']
    _description = 'Users'

    notification_type = fields.Selection([
        ('email', 'Handle by Emails'),
        ('inbox', 'Handle in System')],
        'Notification', required=True, default='email',
        help="Policy on how to handle Chatter notifications:\n"
             "- Handle by Emails: notifications are sent to your email address\n"
             "- Handle in System: notifications appear in your System Inbox")