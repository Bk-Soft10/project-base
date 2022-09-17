from odoo import api, fields, models, _

#######################################################################################################################
######################################################################################################################

class PortalWebsite(models.Model):
    _name = 'portal.website'
    _description = 'Website Portal'

    name = fields.Char(string='Name', required=True, translate=True)
    portal_logo = fields.Binary('Portal Portal')
    group_ids = fields.One2many('portal.group.page', 'portal_id', string='Groups')
    page_ids = fields.One2many('portal.page', 'portal_id', string='Pages')

#######################################################################################################################
######################################################################################################################

class PortalGroupPage(models.Model):
    _name = 'portal.group.page'
    _description = 'Group Page Portal'
    _order = 'sequence'

    name = fields.Char(string='Group Name', required=True, translate=True)
    parent_id = fields.Many2one('portal.group.page', string='Parent')
    portal_id = fields.Many2one('portal.website', string='Website Portal', required=True)
    sequence = fields.Integer(string="Sequence")
    page_ids = fields.One2many('portal.page', 'group_id', string='Pages')
    s_group_id = fields.Many2one('res.groups', string='Group Security')
    active = fields.Boolean(string='Active', default=True)

#######################################################################################################################
######################################################################################################################

class PortalPage(models.Model):
    _name = 'portal.page'
    _description = 'Page Portal'
    _order = 'sequence'

    name = fields.Char(string='Page Name', required=True, translate=True)
    group_id = fields.Many2one('portal.group.page', string='Portal Group', required=True)
    portal_id = fields.Many2one('portal.website', string='Website Portal', related='group_id.portal_id', store=True, readonly=True)
    parent_id = fields.Many2one('portal.page', string='Parent')
    s_group_id = fields.Many2one('res.groups', string='Group Security')
    fa_icon = fields.Char(string='Favicon')
    page_url = fields.Char(string='URL')
    sequence = fields.Integer(string="Sequence")
    active = fields.Boolean(string='Active', default=True)

#######################################################################################################################
######################################################################################################################

class PortalTransactionSetting(models.Model):
    _name = 'portal.transaction.setting'
    _description = 'transaction setting'
    _rec_name = "transaction_label"

    group_id = fields.Many2one('res.groups', string='Group Security', required=1)
    model_id = fields.Many2one('ir.model', string='Model', required=1)
    domain = fields.Char(string='Domain', default="[(1, '=', 1)]", required=1, translate=True)
    after_searching_filter = fields.Char(string='Fillter', default='{}', required=1, translate=True)
    transaction_type = fields.Selection([('follow', 'Follow'), ('validate', 'Validate')],
                                        string='Transaction Type', default='validate', required=1)
    transaction_label = fields.Char(string='Transaction Name', required=1, translate=True)
    transaction_field_number = fields.Many2one('ir.model.fields', string='Transaction No', required=1)
    transaction_field_date = fields.Many2one('ir.model.fields', string='Transaction Date', required=1)
    transaction_approve_method = fields.Char(string='Accept Method', translate=True)
    transaction_refuse_method = fields.Char(string='Refuse Method', translate=True)
    field_refuse_reason = fields.Char(string='Refuse Reason', translate=True)
    details_url = fields.Char(string='URL', translate=True)
    display_button_accept = fields.Boolean(string='Display Accept Method', default=True)
    display_button_refuse = fields.Boolean(string='Display Refuse Method', default=True)
    display_button_details = fields.Char(string='Link', default=False, translate=True)
    active = fields.Boolean(string='Active', default=True)

    @api.onchange('model_id', 'transaction_field_number', 'transaction_field_date')
    def onchange_model_id(self):
        """Onchange model id."""
        res = dict()
        ids = self.model_id and self.model_id.field_id.ids or [-1]
        res.update(domain={'transaction_field_number': [('id', 'in', ids)],
                           'transaction_field_date': [('id', 'in', ids),
                                                      ('ttype', 'in', ('date', 'datetime'))]})
        return res
