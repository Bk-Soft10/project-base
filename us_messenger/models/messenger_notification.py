from odoo import api, fields, models
from odoo.addons.mail.tools.discuss import Store


class MessengerNotification(models.Model):
    _name = 'messenger.notification'
    _description = 'Messenger Notification'
    _rec_name = 'messenger_partner_id'

    mail_message_id = fields.Many2one(
        'mail.message',
        string='Message',
        index=True,
        ondelete='cascade',
        required=True,
    )
    messenger_partner_id = fields.Many2one(
        'us.messenger.partner',
        string='Messenger Partner',
        ondelete='cascade',
        required=True,
    )
    notification_type = fields.Selection([], string='Notification Type', required=True)
    notification_status = fields.Selection([
        ('ready', 'Ready'),
        ('sent', 'Sent'),
        ('exception', 'Exception'),
        ('canceled', 'Canceled'),
    ], string='Status', default='ready', required=True)
    failure_reason = fields.Text('Failure Reason')
    author_id = fields.Many2one(
        'res.partner',
        string='Author',
        related='mail_message_id.author_id',
        store=True,
    )

    _sql_constraints = [
        ('mail_message_messenger_partner_unique', 
         'unique(mail_message_id, messenger_partner_id)', 
         'Only one notification per message and messenger partner')
    ]

    def _to_store_defaults(self, target):
        return [
            "id",
            "mail_message_id",
            "notification_type",
            "notification_status",
            "failure_reason",
            Store.One("messenger_partner_id", [
                "id",
                "name",
                Store.One("bot_id", ["id", "name"]),
            ]),
        ]

    def _to_store(self, store, fields=None, **kwargs):
        if fields is None:
            fields = self._to_store_defaults(store.target)
        store.add_records_fields(self, fields)
