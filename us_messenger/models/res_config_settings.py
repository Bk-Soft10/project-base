from odoo import fields, models, _, Command
from odoo import SUPERUSER_ID


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    group_auto_operator_selection = fields.Boolean(string="Automatic operator selection", 
                                                implied_group='us_messenger.auto_operator_selection')
    auto_operator_selection = fields.Boolean(
        string='For relating with group_auto_operator_selection',
        config_parameter='us_messenger.auto_operator_selection',
        related='group_auto_operator_selection')
    is_add_new_operators_to_channel = fields.Boolean(string="Add new operators to old channels",
                                                config_parameter="us_messenger.add_new_operators_to_channel",
                                                default=True)
    
    def set_values(self):
        before = self.env.user.has_group('us_messenger.auto_operator_selection')
        super(ResConfigSettings, self).set_values()
        after = self.env.user.has_group('us_messenger.auto_operator_selection')
        if before != after:
            if after:
                channels = self.env['discuss.channel'].search([('messenger_operator_id','=',self.env['res.users'].browse(SUPERUSER_ID).partner_id.id)])
                if channels:
                    channels.write({'messenger_operator_id':False})
            else:
                channels = self.env['discuss.channel'].search([('messenger_operator_id','!=',False), ('channel_type','like', 'us_messenger_')])
                for channel in channels:
                    if not channel.messenger_partner_id:
                        continue
                    operators = list(channel.messenger_partner_id.sudo().bot_id.operator_ids.user_id.mapped('partner_id')) # get res.partner of all operators
                    channel.write({
                        'messenger_operator_id':self.env['res.users'].browse(SUPERUSER_ID).partner_id.id,
                        'channel_partner_ids':[Command.link(operator.id) for operator in operators]
                    })
