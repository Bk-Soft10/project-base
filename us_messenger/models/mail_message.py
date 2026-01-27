from odoo import api, models, fields, _
from odoo.addons.mail.tools.discuss import Store


class MailMessage(models.Model):
    _inherit = 'mail.message'

    external_messenger_id = fields.Char(help='External id for messenger', default='')
    document_message_id = fields.Many2one('mail.message',help="Relates a message that was duplicated from the document")
    messenger_notification_ids = fields.One2many(
        'messenger.notification',
        'mail_message_id',
        string='Messenger Notifications',
    )

    def change_author_recipients(self, old_partner, new_partner):
        self.filtered(lambda m: m.author_id.id == old_partner.id).write({'author_id':new_partner.id})
        self.filtered(lambda m: old_partner.id in m.partner_ids.ids).write({'partner_ids':[(4, new_partner.id), (5, old_partner.id)]})
        return True
    
    def _to_store_defaults(self, target):
        field_names = super()._to_store_defaults(target)
        field_names.append(
            Store.Many(
                "messenger_notification_ids",
                value=lambda m: m.sudo().messenger_notification_ids,
            )
        )
        return field_names
    
    def _message_notifications_to_store(self, store):
        super()._message_notifications_to_store(store)
        store.add(
            self,
            [
                Store.Many(
                    "messenger_notification_ids",
                    value=lambda m: m.sudo().messenger_notification_ids,
                ),
            ],
        )
