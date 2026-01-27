# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.addons.mail.tools.discuss import Store


class ResUsers(models.Model):
    _inherit = 'res.users'

    messenger_operator_ids = fields.One2many(
        'us.messenger.operator', 'user_id', string='Messenger operator')

    messenger_nickname = fields.Char(
        string="Messenger nickname",
        default=lambda u: u.name,
        groups="us_messenger.us_messenger_group_user,base.group_erp_manager",
        help="This user nickname is used when no other nickname is specified in the bot settings in the “Operators” tab."
    )

    count_channels = fields.Integer(
        string='Count Channels',
        compute='_compute_count_channels',
        store=True
    )
    has_access_messenger = fields.Boolean(
        compute='_compute_has_access_messenger', 
        string='Has access to Messenger', 
        store=False, 
        readonly=True
    )

    @api.depends("group_ids")
    def _compute_has_access_messenger(self):
        for user in self.sudo():
            user.has_access_messenger = user.has_group('us_messenger.us_messenger_group_user')

    @api.depends('messenger_operator_ids')
    def _compute_count_channels(self):
        for user in self:
            user.count_channels = sum(user.messenger_operator_ids.mapped('channel_count'))

    def _init_store_data(self, store: Store):
        super()._init_store_data(store)
        store.add_global_values(has_access_create_lead=self.env.user.has_group("sales_team.group_sale_salesman"))
