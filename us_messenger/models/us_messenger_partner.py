import logging
from odoo import fields, models, Command, _
from odoo.addons.mail.tools.discuss import Store


_logger = logging.getLogger(__name__)

def get_phone_number(number:str): # 380661234567 -> 380 66 123 4567
    return f"{number[:3]} {number[3:5]} {number[5:8]} {number[8:]}"

class UsMessengerPartner(models.Model):
    _name = 'us.messenger.partner'
    _description = 'Union res_partner and us_messenger_link'
    _order = 'id'

    name = fields.Char('Name', related="partner_id.name")
    partner_id = fields.Many2one('res.partner', ondelete='cascade', required=True)
    bot_id = fields.Many2one('us.messenger.project', ondelete='cascade', required=True)
    external_id = fields.Char('ID User', required=True)
    channel_id = fields.Many2one('discuss.channel', string="Channel", ondelete="set null")
    channel_create_date = fields.Datetime(related='channel_id.create_date', string='Create Date')
    message_count = fields.Char(string='Count Messages', compute="_compute_message_count")
    messenger_operator_id = fields.Many2one('res.partner', string="Operator", related='channel_id.messenger_operator_id')
    username = fields.Char('Username')
    current_step_id = fields.Many2one('us.messenger.script.step', string="Current Step")
    is_hide = fields.Boolean(
        related='bot_id.is_hide_change_operator_user',
        string='Hide button "Change Operator" for operators',
        help="Hide 'Change Operator' for operators in menu 'Operators'. "
            "If active, operators and admins can change operator for channel. "
            "If no active, only admins",
    )
    script_id = fields.Many2one(
        related='bot_id.script_id',
        string='Bot Script',
    )
    type_messenger = fields.Selection(
        related='bot_id.bot_type',
        string='Messenger Type',
        store=True,
    )

    # -------------------------------------------------------------------------
    # COMPUTE METHODS
    # -------------------------------------------------------------------------

    def _compute_message_count(self):
        for record in self:
            record.message_count = len(record.sudo().channel_id.message_ids.ids)

    # -------------------------------------------------------------------------
    # ACTION METHODS
    # -------------------------------------------------------------------------

    def action_become_operator(self):
        user_id = self.env.context.get('uid')
        partner_id = self.env['res.users'].browse(user_id).partner_id.id
        new_member = self.sudo().channel_id.add_members(partner_id, post_joined_message=False)
        new_member.is_pinned = True
        self.sudo().channel_id.write({'messenger_operator_id': partner_id})

    def action_change_operator(self):
        operators = self.sudo().bot_id.operator_ids.user_id.ids
        return {
            'name': _('Change Operator'),
            'view_mode': 'form',
            'res_model': 'us.messenger.discuss.operator.wizard',
            'target': 'new',
            'context': {
                'default_channel_id': self.channel_id.id,
                'default_operators_ids': operators,
                'default_channel_name': self.name,
                'default_operator_id': self.env['res.users'].search([('partner_id','=',self.channel_id.messenger_operator_id.id)]).id
            },
            'type': 'ir.actions.act_window',
        }
    
    # -------------------------------------------------------------------------
    # BUSINESS METHODS
    # -------------------------------------------------------------------------

    @property
    def odoo(self):
        self.ensure_one()
        return self.env['res.partner'].browse(self.partner_id).id

    def link_child_parent(self):
        ''' Search partner by phone number, if find, delete old parter'''
        self.ensure_one()
        
        partner = self.partner_id
        phone = partner.phone

        searching_partner = self.env['res.partner'].search(
            [('phone', '=', phone), ('id', '!=', partner.id)])
        if not searching_partner and phone[0] == '+':
            searching_partner = self.env['res.partner'].search(
                [('phone', '=', phone[1:]), ('id', '!=', partner.id)])
        elif not searching_partner and phone[0] != '+':
            searching_partner = self.env['res.partner'].search(
                [('phone', '=', '+'+phone), ('id', '!=', partner.id)])
        if not searching_partner:
            ch_phone_tmp = phone if phone[0] != '+' else phone[1:] # +380661234567 -> 380661234567
            ch_phone_tmp = get_phone_number(ch_phone_tmp) # 380 66 123 4567
            searching_partner = self.env['res.partner'].search(
                [('phone', '=', ch_phone_tmp), ('id', '!=', partner.id)])
            if not searching_partner:
                searching_partner = self.env['res.partner'].search(
                    [('phone', '=', '+'+ch_phone_tmp), ('id', '!=', partner.id)])

        if len(searching_partner) == 1:
            # del partner. change messages links to searching_partner
            self.unlink_old_partner(searching_partner)
        
        elif len(searching_partner) > 1:
            filtered_partner = searching_partner.filtered(lambda p: p.is_have_messenger)
            if filtered_partner and len(filtered_partner) == 1:
                # del partner. change messages links to searching_partner
                self.unlink_old_partner(filtered_partner)
    
    def unlink_old_partner(self, new_partner):
        self.ensure_one()

        # Skip if partner is internal user
        if new_partner.main_user_id and new_partner.main_user_id._is_internal():
            return
        
        old_partner = self.partner_id
        # change authors and recipients of messages
        messages = self.env['mail.message'].search([('res_id','=',self.channel_id.id), ('model', '=', 'discuss.channel')])
        document_message_ids = messages.filtered(lambda m: m.document_message_id)
        messages.change_author_recipients(old_partner, new_partner)
        self.env['mail.message'].browse(document_message_ids.ids).change_author_recipients(old_partner, new_partner)
        
        # Add new partner to the channel and remove old one
        self.channel_id.add_members([new_partner.id])
        self.channel_id._action_unfollow(partner=old_partner, post_leave_message=False)
        self.channel_id.write({'messenger_client_partner_id': new_partner.id})
        new_partner.write({'category_id': [Command.link(category.id) for category in old_partner.category_id]})
        self.write({'partner_id': new_partner.id})
        old_partner.action_archive()

    # -------------------------------------------------------------------------
    # STORE METHODS
    # -------------------------------------------------------------------------

    def _to_store_defaults(self, target):
        return [
            "id",
            "name",
            "type_messenger",
            Store.One("bot_id", ["id", "name"]),
        ]

    def _to_store(self, store, fields=None, **kwargs):
        if fields is None:
            fields = self._to_store_defaults(store.target)
        store.add_records_fields(self, fields)