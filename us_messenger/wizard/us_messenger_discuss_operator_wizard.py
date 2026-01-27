from odoo import fields, models, api


class UsMessengerDiscussOperatorWizard(models.TransientModel):
    _name = 'us.messenger.discuss.operator.wizard'
    _description = 'Channel Operator Wizard'

    operator_id = fields.Many2one('res.users')
    channel_id = fields.Many2one('discuss.channel')
    channel_name = fields.Char('Channel name', related='channel_id.name')
    operators_ids = fields.Many2many('res.users')

    def action_save_operator(self):
        channel = self.channel_id.sudo()
        operator = self.operator_id
        channel._action_unfollow(channel.messenger_operator_id)
        channel.add_members(operator.partner_id.id, post_joined_message=False)
        channel.write({'messenger_operator_id': operator.partner_id.id})
