from odoo import fields, models


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    us_messenger_channel_id = fields.Many2one(
        'discuss.channel',
        string='Messenger Channel',
        help='The messenger channel from which this lead was created.',
        readonly=True,
        index='btree_not_null',
    )
