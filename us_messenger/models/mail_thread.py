from odoo import models
from markupsafe import Markup

class MailThread(models.AbstractModel):

    _inherit = 'mail.thread'

    def _get_message_create_valid_field_names(self):
        result = super(MailThread, self)._get_message_create_valid_field_names()
        result.add('document_message_id')
        result.add('external_messenger_id')
        return result
    
    def message_post(self, **kwargs):
        if kwargs.get('body', False):
            body = kwargs.get('body', False)
            if not isinstance(body, Markup):
                kwargs['body'] = Markup(body)
        return super(MailThread, self).message_post(**kwargs)