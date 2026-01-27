from odoo import api, models, fields, _, Command
from odoo.addons.mail.tools.discuss import Store


class ResPartner(models.Model):
    _inherit = 'res.partner'

    messenger_partner_ids = fields.One2many(
        'us.messenger.partner', 
        'partner_id',
        string='Messengers contacts',
    )
    is_have_messenger = fields.Boolean(
        'Have messenger', 
        compute="_get_is_messenger", 
        store=True,
    )
    
    # -------------------------------------------------------------------------
    # COMPUTE METHODS
    # -------------------------------------------------------------------------

    @api.depends('messenger_partner_ids')
    def _get_is_messenger(self):
        for rec in self:
            rec.is_have_messenger = len(rec.messenger_partner_ids) > 0
    
    # -------------------------------------------------------------------------
    # LOW-LEVEL METHODS
    # -------------------------------------------------------------------------

    def unlink(self):
        partners_with_messenger = self.filtered('is_have_messenger')
        partners_with_messenger.messenger_partner_ids.unlink()
        return super().unlink()

    def action_archive(self):
        if messenger_partner := self.filtered('is_have_messenger'):
            partner_channels = self.env['discuss.channel'].search(
                [('messenger_client_partner_id', 'in', messenger_partner.ids)]
            )
            if partner_channels:
                partner_channels.action_archive()
        return super().action_archive()

    def action_unarchive(self):
        if messenger_partner := self.filtered('is_have_messenger'):
            partner_channels = self.env['discuss.channel'].search([
                ('messenger_client_partner_id', 'in', messenger_partner.ids),
                ('active', '=', False),
            ])
            if partner_channels:
                partner_channels.action_unarchive()

        return super().action_unarchive()
    
    # -------------------------------------------------------------------------
    # HELPERS
    # -------------------------------------------------------------------------

    def _to_store_defaults(self, target):
        return super()._to_store_defaults(target) + [
            Store.Attr("is_have_messenger")
        ]

    def get_general_params(self, bot) -> dict:
        category_id = self.env.ref(f'us_{bot.bot_type}.res_partner_category_{bot.bot_type}').id
        return {
            'category_id': [Command.link(category_id)]
        }
