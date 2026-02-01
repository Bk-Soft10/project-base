from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError

#################################################################################################################
#################################################################################################################

class SaleRfqWizard(models.TransientModel):
    _name = 'sale.rfq.wizard'
    _description = 'Sale RFQ Wizard'

    def _get_hr_responsible_domain(self):
        return "[('share', '=', False), ('company_ids', 'in', company_id), ('all_group_ids', 'in', %s)]" % self.env.ref('hr.group_hr_user').id

    sale_id = fields.Many2one('sale.order', string='Request Sale', required=True, copy=False)
    warehouse_id = fields.Many2one(related='sale_id.warehouse_id', store=True)
    picking_type_id = fields.Many2one('stock.picking.type', string='Picking Type', copy=False, required=True,
                                   domain="[('code', 'in', ['incoming']), ('warehouse_id', '=', warehouse_id)]")
    line_ids = fields.Many2many('sale.order.line', string='Order Lines', copy=False)
    user_id = fields.Many2one('res.users', string='Purchase User', copy=False)

    @api.onchange('warehouse_id')
    @api.depends('warehouse_id')
    def _change_warehouse_record(self):
        for rec in self:
            rec_su = rec.sudo()
            sale_rec = rec_su.sale_id
            wh_st = rec_su.warehouse_id if rec_su.warehouse_id else sale_rec and sale_rec.warehouse_id or None
            picking_type = wh_st and wh_st.in_type_id or None
            if picking_type:
                rec_su.picking_type_id = picking_type.id

    def action_validate(self):
        self.ensure_one()
        rec_su = self.sudo()
        doc_rec = rec_su.attachment_id
        action_ai = rec_su.ai_action_id
        src_record = doc_rec._get_attachment_record() if doc_rec else False
        ai_data = rec_su.ai_data_ids
        s_data = ai_data.filtered(lambda x: x.can_update and x.action_field_id and x.select) if ai_data else False
        close_act = {'type': 'ir.actions.client', 'tag': 'reload'} or {'type': 'ir.actions.act_window_close'}
        if doc_rec and src_record and ai_data:
            if action_ai:
                ai_data_result = json.load(rec_su.ai_data_result) if rec_su.ai_data_result else {}
                pass_vals = dict(attachment_rec=doc_rec, src_record=src_record, ai_data=ai_data_result)
                res = action_ai._run_action(params=pass_vals)
                res_message = _("AI Call Action Successful!") if res else _("AI Call Action Failed!")
                res_type = 'success' if res else 'warning'
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'message': res_message,
                        'type': res_type,
                        'sticky': False,
                        'next': close_act,
                    }
                }
            if s_data:
                s_data.action_selected_data_fields_update()
        return close_act

    def action_close(self):
        return {'type': 'ir.actions.client', 'tag': 'reload'} or {'type': 'ir.actions.act_window_close'}

