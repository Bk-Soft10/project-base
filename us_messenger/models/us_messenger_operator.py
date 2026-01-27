from odoo import api, fields, models

MESSENGER_TYPES = ["telegram", "viber", "whatsapp_twilio", "instagram"]


class UsMessengerOperator(models.Model):
    _name = "us.messenger.operator"
    _description = "Operators"

    name = fields.Char(related='user_id.name')
    user_id = fields.Many2one('res.users', string="User", required=True)
    bot_id = fields.Many2one('us.messenger.project', string="Bot", ondelete='cascade')
    nickname = fields.Char('User nickname')
    priority = fields.Integer('Priority', default=1)
    channel_count = fields.Integer(compute='_compute_channel_count', string='Channel count')
    partner_id = fields.Many2one('res.partner', related='user_id.partner_id', store=True)
    messenger_type = fields.Selection(related='bot_id.bot_type')
    avatar_128 = fields.Image(related="user_id.avatar_128")
    
    # -------------------------------------------------------------------------
    # COMPUTE METHODS
    # -------------------------------------------------------------------------

    def _compute_channel_count(self):
        for record in self:
            record.channel_count = self.env['us.messenger.partner'].search_count(
                [
                    ('bot_id', '=', record.bot_id.id), 
                    ('messenger_operator_id', '=', record.user_id.partner_id.id),
                    ('channel_id', '!=', False)
                ]
            )

    # -------------------------------------------------------------------------
    # ACTION METHODS
    # -------------------------------------------------------------------------

    def action_operator_channels(self):
        user_partner_id = self.user_id.partner_id.id
        if not user_partner_id:
            return
        channels_by_operator = self.env['discuss.channel'].sudo().search([('messenger_operator_id', '=', user_partner_id)])
        view_id = self.env.ref('us_messenger.discuss_channel_view_list').id

        return {
            'name': 'Messenger Channels',
            'res_model': 'us.messenger.partner',
            'view_mode': 'list',
            'domain': [('channel_id', 'in', channels_by_operator.ids)],
            'type': 'ir.actions.act_window',
            'view_id': view_id,
        }

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('user_id') and not vals.get('nickname'):
                user = self.env['res.users'].browse(vals['user_id'])
                if user.messenger_nickname:
                    vals['nickname'] = user.messenger_nickname
        return super(UsMessengerOperator, self).create(vals_list)
